"""GDScript file size gate: every first-party ``.gd`` file is capped."""

from __future__ import annotations

from ci_common import ROOT, Result, count_lines, load_policy, read_text, relative

NAME = "gdscript_size"


def check() -> Result:
    result = Result(name=NAME)
    policy = load_policy()
    limit = int(policy["max_gdscript_lines"])
    roots = policy.get("gdscript_roots", ["scripts", "tests"])

    paths = []
    for root in roots:
        folder = ROOT / root
        if folder.is_dir():
            paths.extend(sorted(folder.rglob("*.gd")))
    if not paths:
        result.error(f"未找到任何 GDScript（扫描目录: {roots}）")
        return result

    oversized = 0
    for path in paths:
        lines = count_lines(read_text(path))
        if lines > limit:
            oversized += 1
            result.error(f"{relative(path)}: {lines} 行，超过 {limit} 行上限")
    result.note(f"扫描 {len(paths)} 个 .gd 文件，上限 {limit} 行")
    if not oversized:
        result.note("所有 .gd 文件均在行数上限内")
    return result


CHECKS = [(NAME, check)]


if __name__ == "__main__":
    import sys

    from ci_common import main_for_module

    sys.exit(main_for_module(CHECKS))
