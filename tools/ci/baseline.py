"""Create or refresh ``ci/baseline_snapshot.json``.

The snapshot freezes:

* the policy that future changes may only tighten against;
* the protected test cases and test files that may never be deleted;
* a content snapshot of the project used for local scope/budget checks while
  the repository has no git history.

Refreshing is a human-approved operation (``--trusted`` is required).  When the
project is connected to git, GitHub Actions uses the authorative
``--base/--head`` diff instead and this file is only a local fallback.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from ci_common import (
    BASELINE_PATH,
    ROOT,
    count_lines,
    is_binary_file,
    iter_project_files,
    load_json,
    load_policy,
    relative,
    sha256_bytes,
)


def _manifest_cases() -> dict[str, list[str]]:
    path = ROOT / "tests/protected_test_cases.json"
    if not path.is_file():
        return {}
    data = load_json(path)
    files: dict[str, list[str]] = {}
    for name, cases in (data.get("files") or {}).items():
        files[str(name)] = [str(case) for case in cases]
    legacy_file = data.get("file")
    if legacy_file:
        bucket = files.setdefault(str(legacy_file), [])
        for case in data.get("required_assertions", []):
            if case not in bucket:
                bucket.append(str(case))
    return files


def _test_files() -> list[str]:
    tests_dir = ROOT / "tests"
    if not tests_dir.is_dir():
        return []
    return sorted(relative(path) for path in tests_dir.rglob("*.gd"))


def build_snapshot() -> dict:
    policy = load_policy()
    files: dict[str, dict] = {}
    for path in iter_project_files():
        if path == BASELINE_PATH:
            continue
        try:
            payload = path.read_bytes()
        except OSError:
            continue
        rel = relative(path)
        # Binary files contribute 0 diff lines: their content is not diffable and
        # must not inflate the 2400-line budget (e.g. a 7MB font).  Only the
        # file-count budget and sha256 comparison apply to them.
        entry: dict = {"sha256": sha256_bytes(payload), "lines": 0}
        if is_binary_file(path, payload):
            entry["binary"] = True
        else:
            text = payload.decode("utf-8")
            entry["text"] = text
            entry["lines"] = count_lines(text)
        files[rel] = entry
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "note": (
            "Frozen CI baseline. policy/protected_cases must never be weakened; "
            "files is the local scope baseline. Refresh only with human approval: "
            "python tools/ci/baseline.py --trusted --force"
        ),
        "policy": policy,
        "protected_cases": _manifest_cases(),
        "test_files": _test_files(),
        "files": files,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create/refresh CI baseline snapshot.")
    parser.add_argument("--trusted", action="store_true", help="确认已获得人工批准")
    parser.add_argument("--force", action="store_true", help="覆盖已有基线快照")
    args = parser.parse_args(argv)
    if not args.trusted:
        print(
            "拒绝执行：刷新基线需要人工批准。确认后加 --trusted（CI 中由 git 历史提供权威基线）。",
            file=sys.stderr,
        )
        return 2
    if BASELINE_PATH.exists() and not args.force:
        print(
            f"{relative(BASELINE_PATH)} 已存在；如确需刷新请加 --force。",
            file=sys.stderr,
        )
        return 2
    snapshot = build_snapshot()
    BASELINE_PATH.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(
        f"已写入 {relative(BASELINE_PATH)}: "
        f"{len(snapshot['files'])} 文件, "
        f"{sum(len(cases) for cases in snapshot['protected_cases'].values())} 受保护用例, "
        f"gdtoolkit {snapshot['policy'].get('gdtoolkit_version')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
