"""Policy tightening gate: rules may only get stricter over time.

Compared against the frozen policy copy in ``ci/baseline_snapshot.json`` (or
``git show BASE:ci/policy.json`` in the GitHub job).  The gate fails when the
current policy:

* raises an upper bound (document characters, file/line budgets, GDScript
  limits, duplicate block size, research document warning size, retry rounds);
* adds an allowed path/prefix that is not covered by the baseline whitelist;
* adds an asset ignore rule, research glob or versioned doc exemption;
* removes a CI policy path, core document or protected file from the policy;
* changes the policy approver or the pinned gdtoolkit version.
"""

from __future__ import annotations

import argparse
import json
import sys

from ci_common import BASELINE_PATH, POLICY_PATH, Result, load_json, load_policy, run

NAME = "policy_tightening"

UPPER_BOUND_KEYS = [
    "max_core_doc_chars",
    "max_changed_files",
    "max_diff_lines",
    "max_gdscript_lines",
    "max_cyclomatic_complexity",
    "duplicate_block_lines",
    "duplicate_paragraph_min_chars",
    "research_doc_warn_bytes",
    "max_rounds",
]
SUPERSET_KEYS = ["core_docs", "policy_paths", "version_docs"]
SUBSET_KEYS = ["asset_ignore_suffixes", "asset_ignore_files", "asset_ignore_prefixes"]
FROZEN_KEYS = ["policy_approver", "gdtoolkit_version"]


def _policy_at(revision: str) -> dict:
    completed = run(["git", "show", f"{revision}:ci/policy.json"], timeout=120)
    if completed.returncode != 0:
        raise RuntimeError(
            f"无法读取 {revision}:ci/policy.json: {completed.stderr.strip()[:300]}"
        )
    return json.loads(completed.stdout)


def _compare(previous: dict, current: dict, result: Result) -> None:
    for key in UPPER_BOUND_KEYS:
        if key not in previous:
            continue
        if key not in current:
            result.error(f"政策缺少阈值键（视同放宽）: {key}")
            continue
        try:
            if int(current[key]) > int(previous[key]):
                result.error(
                    f"{key} 只能持平或收紧: {previous[key]} -> {current[key]}"
                )
        except (TypeError, ValueError):
            result.error(f"{key} 不是整数: {current[key]!r}")

    for key in SUPERSET_KEYS:
        missing = sorted(set(previous.get(key, [])) - set(current.get(key, [])))
        if missing:
            result.error(f"{key} 移除了条目（放宽保护）: {', '.join(missing)}")

    for key in SUBSET_KEYS:
        added = sorted(set(current.get(key, [])) - set(previous.get(key, [])))
        if added:
            result.error(f"{key} 新增豁免（放宽检查）: {', '.join(added)}")

    for key in FROZEN_KEYS:
        if key in previous and current.get(key) != previous.get(key):
            result.error(
                f"{key} 已被固定，不得修改: {previous.get(key)!r} -> {current.get(key)!r}"
            )

    baseline_prefixes = list(previous.get("allowed_prefixes", []))
    for prefix in current.get("allowed_prefixes", []):
        covered = any(prefix == old or prefix.startswith(old) for old in baseline_prefixes)
        if not covered:
            result.error(f"新增白名单前缀（放宽范围）: {prefix}")

    baseline_files = set(previous.get("allowed_files", []))
    for path in current.get("allowed_files", []):
        if path in baseline_files:
            continue
        covered = any(path.startswith(old) for old in baseline_prefixes)
        if not covered:
            result.error(f"新增白名单文件（放宽范围）: {path}")

    for key in ("research_doc_globs",):
        added = sorted(set(current.get(key, [])) - set(previous.get(key, [])))
        if added:
            result.error(f"{key} 新增豁免（放宽字数检查）: {', '.join(added)}")


def check(base: str | None = None) -> Result:
    result = Result(name=NAME)
    current = load_policy()

    previous: dict | None = None
    mode = ""
    if base:
        try:
            previous = _policy_at(base)
            mode = f"git {base[:10]}"
        except RuntimeError as exc:
            result.error(str(exc))
            return result
    elif BASELINE_PATH.is_file():
        snapshot = load_json(BASELINE_PATH)
        previous = snapshot.get("policy")
        mode = "ci/baseline_snapshot.json"
    else:
        result.note("尚无政策基线快照：按首次基线引入处理（不阻断）")
        return result

    if not isinstance(previous, dict) or not previous:
        result.error("政策基线快照缺少 policy 内容")
        return result

    _compare(previous, current, result)
    result.note(
        f"对比 {mode}：阈值/白名单/豁免/固定项仅允许持平或收紧"
    )
    return result


CHECKS = [(NAME, check)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Policy tightening gate.")
    parser.add_argument("--base", default=None)
    args = parser.parse_args()
    gate = check(args.base)
    from ci_common import print_result

    print_result(gate, 0.0, verbose=True)
    sys.exit(0 if gate.ok else 1)
