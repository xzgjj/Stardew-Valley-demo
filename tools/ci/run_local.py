"""One-command local CI runner.

Runs every gate, prints one PASS/FAIL line plus elapsed time per check, retries
failed checks up to ``max_rounds`` (hard cap 3) and prints a summary with exit
code 0/1.  Failure evidence is written to a temporary directory whose path is
printed at the end.

Examples::

    python tools/ci/run_local.py
    python tools/ci/run_local.py --rounds 1
    python tools/ci/run_local.py --only docs,assets
    python tools/ci/run_local.py --skip scope,policy_tightening
    python tools/ci/run_local.py --list
    python tools/ci/run_local.py --bootstrap
"""

from __future__ import annotations

import argparse
import importlib
import sys
import tempfile
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from ci_common import (  # noqa: E402
    ROOT,
    Result,
    expected_godot_build,
    gdtoolkit_version,
    godot_version,
    load_policy,
    print_result,
    python_version,
    resolve_gdtoolkit_tool,
    resolve_godot,
    tool_version,
)

MODULE_ORDER = [
    "check_docs",
    "check_protected_tests",
    "check_assets",
    "check_gdscript_size",
    "check_complexity",
    "check_duplicate_blocks",
    "check_unused_scripts",
    "check_lint",
    "check_scope",
    "check_policy_tightening",
    "check_godot",
]


def discover_checks() -> list[tuple[str, object]]:
    entries: list[tuple[str, object]] = []
    for module_name in MODULE_ORDER:
        module = importlib.import_module(module_name)
        checks = getattr(module, "CHECKS", None)
        if not checks:
            raise RuntimeError(f"{module_name} 未导出 CHECKS")
        entries.extend((str(name), func) for name, func in checks)
    return entries


def print_header(policy: dict) -> None:
    print("Stardew Valley demo - local CI", flush=True)
    print(f"  project   : {ROOT}")
    print(f"  python    : {python_version()}")
    try:
        executable, _tried = resolve_godot(policy)
        actual = godot_version(executable) if executable else "未找到"
        expected = expected_godot_build(policy) or "?"
        print(f"  godot     : {executable or '未找到'} ({actual} / 期望 {expected})")
    except Exception as exc:  # noqa: BLE001 - header must never abort the run
        print(f"  godot     : 探测异常 {exc.__class__.__name__}: {exc}")
    try:
        gdlint, source = resolve_gdtoolkit_tool("gdlint")
        installed = tool_version(gdlint) if gdlint else "未安装"
        print(
            f"  gdtoolkit : {installed} ({source}) / 固定 {gdtoolkit_version(policy)}"
        )
    except Exception as exc:  # noqa: BLE001
        print(f"  gdtoolkit : 探测异常 {exc.__class__.__name__}: {exc}")
    print(f"  policy    : ci/policy.json (max_rounds={policy.get('max_rounds', 3)})")
    print("", flush=True)


def write_evidence(directory: Path, result: Result, crash: str | None) -> None:
    lines = [
        f"gate: {result.name}",
        f"status: {'PASS' if result.ok else 'FAIL'}",
        "",
        "[errors]",
        *result.errors,
        "",
        "[warnings]",
        *result.warnings,
        "",
        "[notes]",
        *result.notes,
    ]
    if crash:
        lines += ["", "[traceback]", crash]
    (directory / f"{result.name}.log").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the full local CI suite.")
    parser.add_argument("--rounds", type=int, default=None, help="最多重试轮数（上限 3）")
    parser.add_argument("--only", default=None, help="只运行指定检查（逗号分隔）")
    parser.add_argument("--skip", default=None, help="跳过指定检查（逗号分隔）")
    parser.add_argument("--verbose", "-v", action="store_true", help="打印每项 note")
    parser.add_argument("--list", action="store_true", help="列出检查名后退出")
    parser.add_argument("--bootstrap", action="store_true", help="先把 gdtoolkit 安装到 .ci-venv")
    args = parser.parse_args(argv)

    policy = load_policy()
    max_rounds = int(policy.get("max_rounds", 3))
    rounds = max_rounds if args.rounds is None else args.rounds
    if rounds < 1:
        print("--rounds 必须 >= 1", file=sys.stderr)
        return 2
    if rounds > max_rounds:
        print(
            f"拒绝执行：本地 runner 最多 {max_rounds} 轮（--rounds {rounds} 超限）。"
            "超限会掩盖不稳定失败，请在上一轮证据基础上定位根因。",
            file=sys.stderr,
        )
        return 2

    if args.bootstrap:
        from bootstrap_toolchain import bootstrap

        code = bootstrap()
        if code != 0:
            print("工具链安装失败，停止运行。", file=sys.stderr)
            return code

    try:
        entries = discover_checks()
    except Exception as exc:  # noqa: BLE001
        print(f"无法加载检查模块: {exc}", file=sys.stderr)
        return 2

    only = {item.strip() for item in (args.only or "").split(",") if item.strip()}
    skip = {item.strip() for item in (args.skip or "").split(",") if item.strip()}
    names = [name for name, _func in entries]
    unknown = sorted((only | skip) - set(names))
    if unknown:
        print(f"未知检查名: {', '.join(unknown)}\n可用检查: {', '.join(names)}", file=sys.stderr)
        return 2
    entries = [
        (name, func)
        for name, func in entries
        if (not only or name in only) and name not in skip
    ]
    if not entries:
        print("没有选中任何检查。", file=sys.stderr)
        return 2
    if args.list:
        print("\n".join(name for name, _func in entries))
        return 0

    print_header(policy)

    evidence_dir: Path | None = None

    def record(result: Result, crash: str | None = None) -> None:
        nonlocal evidence_dir
        if result.ok and crash is None:
            return
        if evidence_dir is None:
            evidence_dir = Path(tempfile.mkdtemp(prefix="stardew-ci-"))
        write_evidence(evidence_dir, result, crash)

    results: dict[str, Result] = {}
    elapsed: dict[str, float] = {}
    pending = [name for name, _func in entries]
    round_number = 0
    started_all = time.perf_counter()

    while pending and round_number < rounds:
        round_number += 1
        print(f"=== Round {round_number}/{rounds} ===", flush=True)
        still_failing: list[str] = []
        lookup = dict(entries)
        for name in list(pending):
            func = lookup[name]
            started = time.perf_counter()
            crash: str | None = None
            try:
                result = func()  # type: ignore[operator]
                if not isinstance(result, Result):
                    raise TypeError(f"{name} 返回了 {type(result).__name__} 而非 Result")
            except Exception as exc:  # noqa: BLE001 - a crashing gate is a failing gate
                crash = traceback.format_exc()
                result = Result(
                    name=name,
                    errors=[f"gate 崩溃: {exc.__class__.__name__}: {exc}"],
                )
            result.name = name
            elapsed[name] = time.perf_counter() - started
            results[name] = result
            print_result(result, elapsed[name], verbose=args.verbose)
            record(result, crash)
            if not result.ok:
                still_failing.append(name)
        pending = still_failing
        if pending and round_number < rounds:
            print(
                f"{len(pending)} 项失败，重试（{round_number + 1}/{rounds}）: "
                f"{', '.join(pending)}",
                flush=True,
            )
        print("", flush=True)

    total_elapsed = time.perf_counter() - started_all
    passed = sum(1 for result in results.values() if result.ok)
    failed = len(results) - passed
    warnings_total = sum(len(result.warnings) for result in results.values())

    print("=" * 72)
    print(" SUMMARY")
    for name, _func in entries:
        result = results.get(name)
        if result is None:
            continue
        status = "PASS" if result.ok else "FAIL"
        detail = ""
        if result.errors:
            detail = f"  {len(result.errors)} error(s)"
        elif result.warnings:
            detail = f"  {len(result.warnings)} warning(s)"
        print(f" {status}  {name:<20} {elapsed.get(name, 0.0):6.2f}s{detail}")
    print("-" * 72)
    print(
        f" Totals: {passed} passed, {failed} failed, {warnings_total} warning(s) | "
        f"rounds {round_number}/{rounds} | {total_elapsed:.2f}s"
    )
    if pending and round_number >= rounds:
        print(
            f" 重试上限 {rounds} 轮已用尽，停止重试；请按上面的失败证据修复根因，"
            "不要无证据反复重跑。"
        )
    if evidence_dir is not None:
        print(f" 证据日志（失败项完整输出）: {evidence_dir}")
    passed_all = failed == 0 and not pending
    print(f" RESULT: {'PASS' if passed_all else 'FAIL'}")
    return 0 if passed_all else 1


if __name__ == "__main__":
    sys.exit(main())
