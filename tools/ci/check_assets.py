"""Asset provenance gate.

Every file under ``assets/`` must be registered in ``docs/asset_manifest.md``
inside the licence table, and the licence column must not be empty.  Generated
Godot metadata (``*.import`` / ``*.uid``), the assets README and the attached
licence texts under ``assets/licenses/`` are exempt because they are derived
or are the licence evidence itself (documented in docs/ci_rules.md).
"""

from __future__ import annotations

import re

from ci_common import ROOT, Result, load_policy, read_text, relative

NAME = "assets"
PLACEHOLDERS = {"", "-", "—", "–", "待补", "待定", "tbd", "todo", "?", "无", "n/a", "none"}


def _ignored(rel: str, policy: dict) -> bool:
    lower = rel.lower()
    for suffix in policy.get("asset_ignore_suffixes", []):
        if lower.endswith(suffix.lower()):
            return True
    if rel in policy.get("asset_ignore_files", []):
        return True
    for prefix in policy.get("asset_ignore_prefixes", []):
        if rel.startswith(prefix):
            return True
    return False


def _licence_column(manifest_text: str, headers: list[str]) -> int | None:
    for line in manifest_text.splitlines():
        if line.count("|") < 2:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        lowered = [cell.casefold() for cell in cells]
        for header in headers:
            needle = header.casefold()
            for index, cell in enumerate(lowered):
                if needle in cell:
                    return index
    return None


def _licence_cell(line: str, column: int) -> str:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if column >= len(cells):
        return ""
    return cells[column]


def check() -> Result:
    result = Result(name=NAME)
    policy = load_policy()
    manifest_rel = policy.get("asset_manifest", "docs/asset_manifest.md")
    manifest_path = ROOT / manifest_rel

    if not manifest_path.is_file():
        result.error(
            f"素材登记清单缺失: {manifest_rel}（assets/ 下每个文件都需登记许可字段）"
        )
        return result
    text = read_text(manifest_path)
    headers = policy.get("asset_manifest_license_headers", ["许可", "License", "授权"])
    column = _licence_column(text, headers)
    if column is None:
        result.error(
            f"{manifest_rel}: 未找到许可表头（需包含 {'/'.join(headers)} 列）"
        )
        return result

    asset_files: list[str] = []
    for root in policy.get("asset_roots", ["assets"]):
        folder = ROOT / root
        if not folder.is_dir():
            result.warn(f"素材目录不存在: {root}")
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            rel = relative(path)
            if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
                continue
            if _ignored(rel, policy):
                continue
            asset_files.append(rel)

    if not asset_files:
        result.note("assets/ 下没有需要登记的素材文件")
        return result

    missing: list[str] = []
    unlicensed: list[str] = []
    for rel in asset_files:
        line = next(
            (row for row in text.splitlines() if rel in row),
            None,
        )
        if line is None:
            missing.append(rel)
            continue
        value = _licence_cell(line, column).casefold().strip()
        if value in PLACEHOLDERS or re.fullmatch(r"[-—–\s]*", value):
            unlicensed.append(rel)

    for rel in missing[:20]:
        result.error(f"素材未登记: {rel}")
    if len(missing) > 20:
        result.error(f"... 其余 {len(missing) - 20} 个未登记素材未逐条列出")
    for rel in unlicensed[:20]:
        result.error(f"素材许可字段为空: {rel}")
    if len(unlicensed) > 20:
        result.error(f"... 其余 {len(unlicensed) - 20} 个空许可素材未逐条列出")

    result.note(
        f"检查 {len(asset_files)} 个素材文件（已豁免 .import/.uid/README/许可文本），"
        f"许可列索引 {column}"
    )
    return result


CHECKS = [(NAME, check)]


if __name__ == "__main__":
    import sys

    from ci_common import main_for_module

    sys.exit(main_for_module(CHECKS))
