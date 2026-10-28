"""gdlint + gdformat gate using the pinned gdtoolkit build.

The fixed version is read from ``ci/policy.json`` (``gdtoolkit_version``) and
must match the locally installed tool; CI.md records the same pin.

Tools are resolved from ``.ci-venv`` first (developer machines) and from
``PATH`` second (GitHub runner).  Optional lint configuration is looked up in
``ci/`` (``gdlintrc`` / ``.gdlintrc``, ``gdformatrc`` / ``.gdformatrc``): when
present the tools run with ``ci/`` as working directory because gdtoolkit
searches for its config upwards from the current directory.  Any config change
lives under ``ci/`` and is therefore covered by the policy approval job; the
default (strict) gdtoolkit configuration is used when no file is present.
"""

from __future__ import annotations

import re

from ci_common import (
    CI_DIR,
    ROOT,
    Result,
    excerpt,
    load_policy,
    print_result,
    resolve_gdtoolkit_tool,
    run,
    tool_version,
)

NAME = "gdlint"
VERSION_RE = re.compile(r"(\d+\.\d+\.\d+)")


def _config_cwd(names: list[str]):
    for name in names:
        if (CI_DIR / name).is_file():
            return CI_DIR
    return ROOT


def _roots_for_cwd(cwd) -> list[str]:
    policy = load_policy()
    roots = policy.get("gdscript_roots", ["scripts", "tests"])
    if cwd == ROOT:
        return list(roots)
    import os

    return [os.path.relpath(str(ROOT / root), str(cwd)) for root in roots]


def _resolve(name: str, config_names: list[str], result: Result):
    policy = load_policy()
    executable, source = resolve_gdtoolkit_tool(name)
    if not executable:
        pinned = policy.get("gdtoolkit_version", "")
        result.error(
            f"未找到 {name}。请运行: python tools/ci/bootstrap_toolchain.py "
            f"（安装 gdtoolkit=={pinned} 到 .ci-venv），或执行 "
            f"python -m venv .ci-venv && .ci-venv/Scripts/python.exe -m pip install gdtoolkit=={pinned}"
        )
        return None, None, None
    installed = tool_version(executable)
    match = VERSION_RE.search(installed)
    expected = str(policy.get("gdtoolkit_version", ""))
    if match and expected and match.group(1) != expected:
        result.error(
            f"{name} 版本 {match.group(1)} 与 ci/policy.json 固定版本 {expected} 不一致"
            f"（来源: {source}）"
        )
    cwd = _config_cwd(config_names)
    return executable, cwd, installed


def _bom_files() -> list[str]:
    """gdtoolkit cannot parse a UTF-8 BOM; surface a precise error first."""
    policy = load_policy()
    bom: list[str] = []
    for root in policy.get("gdscript_roots", ["scripts", "tests"]):
        folder = ROOT / root
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*.gd")):
            payload = path.read_bytes()
            if payload.startswith(b"\xef\xbb\xbf"):
                bom.append(relative(path))
    return bom


def check_gdlint() -> Result:
    result = Result(name=NAME)
    bom = _bom_files()
    for rel in bom:
        result.error(
            f"{rel}: 文件带 UTF-8 BOM，gdtoolkit 无法解析；请用 UTF-8（无 BOM）重新保存"
        )
    executable, cwd, installed = _resolve(
        "gdlint", ["gdlintrc", ".gdlintrc"], result
    )
    if not executable:
        return result
    roots = _roots_for_cwd(cwd)
    completed = run([executable, *roots], cwd=cwd, timeout=300)
    output = excerpt((completed.stdout or "") + "\n" + (completed.stderr or ""), 25)
    if completed.returncode != 0:
        result.error(f"gdlint 失败（exit {completed.returncode}）:\n{output}")
    result.note(
        f"gdlint {installed or '?'}（来源 {executable}，cwd {cwd}）检查 {', '.join(roots)}"
    )
    return result


def check_gdformat() -> Result:
    result = Result(name="gdformat")
    bom = _bom_files()
    for rel in bom:
        result.error(f"{rel}: 文件带 UTF-8 BOM，gdformat 无法解析；请重存为 UTF-8（无 BOM）")
    executable, cwd, installed = _resolve(
        "gdformat", ["gdformatrc", ".gdformatrc"], result
    )
    if not executable:
        return result
    roots = _roots_for_cwd(cwd)
    completed = run([executable, "--check", *roots], cwd=cwd, timeout=300)
    output = excerpt((completed.stdout or "") + "\n" + (completed.stderr or ""), 25)
    if completed.returncode != 0:
        result.error(
            f"gdformat --check 失败（存在未格式化文件，exit {completed.returncode}）:\n{output}"
        )
    result.note(f"gdformat {installed or '?'}（来源 {executable}）--check {', '.join(roots)}")
    return result


CHECKS = [(NAME, check_gdlint), ("gdformat", check_gdformat)]


if __name__ == "__main__":
    import sys

    from ci_common import main_for_module

    sys.exit(main_for_module(CHECKS))
