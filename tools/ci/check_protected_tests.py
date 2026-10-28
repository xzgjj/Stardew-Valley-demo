"""Protected regression test gate.

``tests/protected_test_cases.json`` is the authoritative list of behaviour
assertions that must survive every change.  The gate fails when:

* a listed case id is missing from the manifest (deleted or renamed),
* a listed case id is no longer present in its test file (weakend/removed),
* a protected test file listed in the frozen baseline snapshot is deleted.

New test files that are not yet registered produce warnings so they can be
added without blocking unrelated work.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ci_common import (
    BASELINE_PATH,
    ROOT,
    Result,
    load_json,
    load_policy,
    read_text,
    relative,
    run,
)

NAME = "protected_tests"
MANIFEST_PATH = ROOT / "tests/protected_test_cases.json"


def _manifest_files(result: Result) -> dict[str, list[str]]:
    if not MANIFEST_PATH.is_file():
        result.error(f"受保护测试清单缺失: {relative(MANIFEST_PATH)}")
        return {}
    data = load_json(MANIFEST_PATH)
    files: dict[str, list[str]] = {}
    for path, cases in (data.get("files") or {}).items():
        files[str(path)] = [str(case) for case in cases]
    legacy_file = data.get("file")
    if legacy_file:
        bucket = files.setdefault(str(legacy_file), [])
        for case in data.get("required_assertions", []):
            if case not in bucket:
                bucket.append(str(case))
    if not files:
        result.error("受保护测试清单没有任何用例（files 为空）")
    return files


def _baseline() -> dict:
    if not BASELINE_PATH.is_file():
        return {}
    return load_json(BASELINE_PATH)


def _git_deleted_tests(result: Result, base: str, head: str) -> None:
    completed = run(["git", "diff", "--name-status", f"{base}...{head}"], timeout=120)
    if completed.returncode != 0:
        result.error(f"git diff 失败（{base}...{head}）: {completed.stderr.strip()[:300]}")
        return
    for row in (completed.stdout or "").splitlines():
        parts = row.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0].strip(), parts[1].strip()
        if status.startswith("D") and path.startswith("tests/") and path.endswith(".gd"):
            result.error(f"测试文件被删除（需人工复核）: {path}")


def check(base: str | None = None, head: str | None = None) -> Result:
    result = Result(name=NAME)
    load_policy()
    files = _manifest_files(result)

    # --- 1. manifest cases must still exist inside their test files ---------
    total_cases = 0
    for path, cases in files.items():
        total_cases += len(cases)
        file_path = ROOT / path
        if not cases:
            result.warn(f"{path} 未登记任何受保护用例")
        if not file_path.is_file():
            result.error(f"受保护测试文件缺失: {path}")
            continue
        source = read_text(file_path)
        for case in cases:
            if f'"{case}"' not in source and case not in source:
                result.error(f"受保护用例缺失/被弱化: {path} :: {case}")

    # --- 2. frozen baseline: cases and test files may only grow -------------
    snapshot = _baseline()
    baseline_cases = snapshot.get("protected_cases", {})
    if baseline_cases:
        for path, cases in baseline_cases.items():
            if path not in files:
                result.error(f"保护清单删除了受保护测试文件: {path}")
            else:
                missing = [case for case in cases if case not in files[path]]
                for case in missing:
                    result.error(f"受保护用例被删除: {path} :: {case}")
    for path in snapshot.get("test_files", []):
        if not (ROOT / path).is_file():
            result.error(f"测试文件被删除（基线中存在）: {path}")

    # --- 3. warn about unprotected new tests --------------------------------
    tests_dir = ROOT / "tests"
    if tests_dir.is_dir():
        for file_path in sorted(tests_dir.rglob("test_*.gd")):
            rel = relative(file_path)
            if rel not in files:
                result.warn(f"新增测试未纳入保护清单（建议登记用例 id）: {rel}")

    # --- 4. optional git history mode (used by the GitHub Actions job) ------
    if base and head:
        _git_deleted_tests(result, base, head)

    result.note(f"{len(files)} 个测试文件 / {total_cases} 个受保护用例")
    return result


CHECKS = [(NAME, check)]


if __name__ == "__main__":
    import argparse

    from ci_common import main_for_module

    parser = argparse.ArgumentParser(description="Protected test case gate.")
    parser.add_argument("--base", default=None)
    parser.add_argument("--head", default=None)
    args, _unknown = parser.parse_known_args()
    if args.base and args.head:
        sys.exit(main_for_module([(NAME, lambda: check(args.base, args.head))]))
    sys.exit(main_for_module(CHECKS))
