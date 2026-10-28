"""Change scope gate.

Two modes are supported:

* ``--base SHA --head SHA`` - authoritative git diff used by GitHub Actions;
* local mode - compare the working tree against the frozen baseline snapshot
  ``ci/baseline_snapshot.json`` (the project is not a git repository yet).
  When no snapshot exists the run is treated as the first baseline
  introduction and does not block.

Both modes enforce the whitelist in ``ci/policy.json`` plus the file and line
budgets.  Changes to CI policy paths are reported but not failed locally:
approval is enforced by the ``policy-approval`` GitHub Actions job.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

from ci_common import (
    BASELINE_PATH,
    ROOT,
    Result,
    count_lines,
    iter_project_files,
    is_binary_file,
    load_json,
    load_policy,
    read_text,
    relative,
    run,
    sha256_bytes,
)

NAME = "scope"
SNAPSHOT_SELF = BASELINE_PATH


def _is_allowed(path: str, policy: dict) -> bool:
    if path in policy.get("allowed_files", []):
        return True
    return any(path.startswith(prefix) for prefix in policy.get("allowed_prefixes", []))


def _diff_lines(before: str, after: str) -> int:
    matcher = difflib.SequenceMatcher(a=before.splitlines(), b=after.splitlines())
    total = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        total += (i2 - i1) + (j2 - j1)
    return total


def _git_changes(base: str, head: str) -> tuple[list[str], int]:
    inside = run(["git", "rev-parse", "--is-inside-work-tree"], timeout=60)
    if inside.returncode != 0:
        raise RuntimeError("当前目录不是 git 仓库，无法使用 --base/--head 模式")
    names = run(
        ["git", "diff", "--name-only", "-z", f"{base}...{head}"], timeout=120
    )
    if names.returncode != 0:
        raise RuntimeError(f"git diff --name-only 失败: {names.stderr.strip()[:300]}")
    paths = [path for path in (names.stdout or "").split("\0") if path]
    numstat = run(["git", "diff", "--numstat", f"{base}...{head}"], timeout=120)
    changed_lines = 0
    for row in (numstat.stdout or "").splitlines():
        parts = row.split("\t")
        if len(parts) < 2:
            continue
        for token in parts[:2]:
            if token.isdigit():
                changed_lines += int(token)
    return paths, changed_lines


def _snapshot_changes() -> tuple[list[str], list[str], list[str], int] | None:
    if not BASELINE_PATH.is_file():
        return None
    snapshot = load_json(BASELINE_PATH)
    baseline_files: dict[str, dict] = snapshot.get("files", {})
    current: dict[str, dict] = {}
    for path in iter_project_files():
        if path == SNAPSHOT_SELF:
            continue
        rel = relative(path)
        try:
            payload = path.read_bytes()
        except OSError:
            continue
        entry: dict = {"sha256": sha256_bytes(payload), "lines": 0}
        if is_binary_file(path, payload):
            entry["binary"] = True
        else:
            text = payload.decode("utf-8")
            entry["text"] = text
            entry["lines"] = count_lines(text)
        current[rel] = entry

    added = sorted(set(current) - set(baseline_files))
    deleted = sorted(set(baseline_files) - set(current))
    modified = sorted(
        rel
        for rel in set(current) & set(baseline_files)
        if current[rel]["sha256"] != baseline_files[rel].get("sha256")
    )

    changed_lines = 0
    for rel in added:
        changed_lines += current[rel]["lines"]
    for rel in deleted:
        changed_lines += int(baseline_files[rel].get("lines", 0))
    for rel in modified:
        before = baseline_files[rel].get("text")
        after = current[rel].get("text")
        if before is None or after is None:
            changed_lines += int(baseline_files[rel].get("lines", 0)) + current[rel][
                "lines"
            ]
        else:
            changed_lines += _diff_lines(before, after)
    return added, deleted, modified, changed_lines


def check(base: str | None = None, head: str | None = None) -> Result:
    result = Result(name=NAME)
    policy = load_policy()

    if base and head:
        try:
            paths, changed_lines = _git_changes(base, head)
        except RuntimeError as exc:
            result.error(str(exc))
            return result
        mode = f"git {base[:10]}...{head[:10]}"
    else:
        snapshot = _snapshot_changes()
        if snapshot is None:
            result.note(
                "首次引入基线快照：跳过范围阻断（基线引入不阻断），"
                "请用 python tools/ci/baseline.py --trusted 建立基线"
            )
            return result
        added, deleted, modified, changed_lines = snapshot
        paths = added + deleted + modified
        mode = f"baseline snapshot（新增 {len(added)} / 删除 {len(deleted)} / 修改 {len(modified)}）"

    outside = [path for path in paths if not _is_allowed(path, policy)]
    for path in outside[:20]:
        result.error(f"改动超出白名单: {path}")
    if len(outside) > 20:
        result.error(f"... 其余 {len(outside) - 20} 个越界文件未逐条列出")

    max_files = int(policy["max_changed_files"])
    max_lines = int(policy["max_diff_lines"])
    if len(paths) > max_files:
        result.error(f"改动文件数 {len(paths)} 超过预算 {max_files}")
    if changed_lines > max_lines:
        result.error(f"增删行数 {changed_lines} 超过预算 {max_lines}")

    protected_paths = policy.get("policy_paths", [])
    touched = [
        path
        for path in paths
        if any(path == item or path.startswith(item) for item in protected_paths)
    ]
    if touched:
        result.warn(
            "本次改动涉及 CI/政策/测试保护文件，需 policy_approver 在 PR 当前 head 上批准: "
            + ", ".join(sorted(touched)[:8])
        )

    result.note(
        f"{mode}: {len(paths)} 文件 / {changed_lines} 行增删 "
        f"（预算 {max_files} 文件 / {max_lines} 行）"
    )
    return result


CHECKS = [(NAME, check)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scope gate.")
    parser.add_argument("--base", default=None)
    parser.add_argument("--head", default=None)
    args = parser.parse_args()
    gate = check(args.base, args.head)
    from ci_common import print_result

    print_result(gate, 0.0, verbose=True)
    sys.exit(0 if gate.ok else 1)
