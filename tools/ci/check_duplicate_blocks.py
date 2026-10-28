"""Duplicate code block gate for GDScript.

A duplicate is a run of ``duplicate_block_lines`` normalised source lines
(whitespace collapsed, blank lines and comments removed) that appears at more
than one location, either across files or repeatedly inside one file.
"""

from __future__ import annotations

import re
from collections import defaultdict

from ci_common import ROOT, Result, load_policy, read_text, relative

NAME = "duplicate_blocks"


def _normalised_lines(path) -> list[str]:
    rows: list[str] = []
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(re.sub(r"\s+", " ", line))
    return rows


def check() -> Result:
    result = Result(name=NAME)
    policy = load_policy()
    size = int(policy["duplicate_block_lines"])
    roots = policy.get("gdscript_roots", ["scripts", "tests"])

    paths = []
    for root in roots:
        folder = ROOT / root
        if folder.is_dir():
            paths.extend(sorted(folder.rglob("*.gd")))

    occurrences: dict[tuple[str, ...], list[tuple[str, int]]] = defaultdict(list)
    for path in paths:
        rows = _normalised_lines(path)
        rel = relative(path)
        for start in range(max(0, len(rows) - size + 1)):
            block = tuple(rows[start : start + size])
            occurrences[block].append((rel, start + 1))

    duplicates = 0
    for block, locations in occurrences.items():
        if len(locations) < 2:
            continue
        duplicates += 1
        if duplicates > 10:
            continue
        rendered = " | ".join(f"{rel}:{line}" for rel, line in locations[:4])
        preview = " / ".join(block[:2])
        result.error(
            f"重复代码块（{size} 行）出现在 {len(locations)} 处: {rendered} :: {preview}"
        )
    if duplicates > 10:
        result.error(f"其余 {duplicates - 10} 处重复代码块未逐条列出")
    if duplicates:
        result.error(
            f"发现 {duplicates} 处重复代码块；请复用函数或说明无法复用的原因"
        )
    result.note(f"扫描 {len(paths)} 个 .gd 文件，重复块阈值 {size} 行")
    return result


CHECKS = [(NAME, check)]


if __name__ == "__main__":
    import sys

    from ci_common import main_for_module

    sys.exit(main_for_module(CHECKS))
