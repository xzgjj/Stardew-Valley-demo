"""Documentation gate: budgets, duplicate paragraphs and version agreement.

Rules implemented (see docs/ci_rules.md):

* every core planning document exists and is at most
  ``max_core_doc_chars`` Unicode characters long;
* normalised duplicate paragraphs (whitespace-collapsed, case-folded) are
  reported inside core documents and research documents;
* research documents (``docs/research_*.md`` / ``docs/reference_*.md``) are
  exempt from the character cap but warn above ``research_doc_warn_bytes`` and
  are still checked for duplicated paragraphs;
* ``GODOT_VERSION.txt``, ``project.godot`` and ``CI.md`` must agree on the
  locked Godot build, and ``CI.md`` must record the pinned gdtoolkit version.
"""

from __future__ import annotations

import re
from pathlib import Path

from ci_common import (
    ROOT,
    Result,
    load_policy,
    read_text,
    relative,
)

NAME = "docs"

PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")
FEATURES_RE = re.compile(r"config/features\s*=\s*PackedStringArray\((?P<items>.*?)\)", re.S)
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+\.[A-Za-z][\w]*\.\w+\.\w+$")


def _normalise(paragraph: str) -> str:
    return re.sub(r"\s+", " ", paragraph).strip().casefold()


def _duplicate_paragraphs(text: str, minimum: int) -> list[tuple[str, int]]:
    seen: dict[str, int] = {}
    duplicates: list[tuple[str, int]] = []
    for raw in PARAGRAPH_SPLIT.split(text):
        normalised = _normalise(raw)
        if len(normalised) < minimum:
            continue
        if normalised in seen:
            preview = " ".join(raw.split())[:80]
            duplicates.append((preview, seen[normalised]))
        else:
            seen[normalised] = len(normalised)
    return duplicates


def check() -> Result:
    result = Result(name=NAME)
    policy = load_policy()

    limit = int(policy["max_core_doc_chars"])
    core_docs: list[str] = policy["core_docs"]
    minimum = int(policy.get("duplicate_paragraph_min_chars", 20))

    # --- core documents: existence, budget, duplicate paragraphs -------------
    for doc in core_docs:
        path = ROOT / doc
        if not path.is_file():
            result.error(
                f"核心文档缺失: {doc}（要求 ≤{limit} 字符，需由负责人创建）"
            )
            continue
        text = read_text(path)
        length = len(text)
        if length > limit:
            result.error(f"{doc}: {length} 字符，超过上限 {limit}")
        result.note(f"{doc}: {length}/{limit} 字符")
        duplicates = _duplicate_paragraphs(text, minimum)
        for preview, _size in duplicates[:5]:
            result.error(f"{doc}: 重复段落（归一化后完全相同）: {preview}")

    # --- research documents: size warning + duplicate paragraph check --------
    warn_bytes = int(policy.get("research_doc_warn_bytes", 20480))
    research_files: list[Path] = []
    for pattern in policy.get("research_doc_globs", []):
        research_files.extend(sorted(ROOT.glob(pattern)))
    seen_paths: set[Path] = set()
    for path in research_files:
        if path in seen_paths or not path.is_file():
            continue
        seen_paths.add(path)
        rel = relative(path)
        size = path.stat().st_size
        if size > warn_bytes:
            result.warn(f"研究文档体积 {size} 字节 > {warn_bytes} 字节: {rel}")
        duplicates = _duplicate_paragraphs(read_text(path), minimum)
        for preview, _size in duplicates[:5]:
            result.error(f"{rel}: 重复段落（归一化后完全相同）: {preview}")
        result.note(f"{rel}: {size} 字节（研究文档，不限字数）")

    # --- version agreement: GODOT_VERSION.txt <-> project.godot <-> CI.md ---
    build = ""
    version_file = ROOT / policy.get("godot_version_file", "GODOT_VERSION.txt")
    if not version_file.is_file():
        result.error("GODOT_VERSION.txt 缺失")
    else:
        build = read_text(version_file).strip()
        if not VERSION_PATTERN.match(build):
            result.error(f"GODOT_VERSION.txt 格式异常: {build!r}")
    if build:
        family = ".".join(build.split(".")[:2])
        project_path = ROOT / "project.godot"
        if not project_path.is_file():
            result.error("project.godot 缺失")
        else:
            project_text = read_text(project_path)
            features = FEATURES_RE.search(project_text)
            if not features:
                result.error("project.godot 缺少 config/features=PackedStringArray(...)")
            else:
                declared = re.findall(r'"(\d+\.\d+)"', features.group("items"))
                if family not in declared:
                    result.error(
                        f"project.godot 特性行未声明 {family}（实际: {declared or '无版本特性'}），"
                        f"与 GODOT_VERSION.txt {build} 不一致"
                    )
                wrong = sorted({item for item in declared if item != family})
                if wrong:
                    result.error(
                        f"project.godot 声明了与 GODOT_VERSION.txt 冲突的版本特性: {wrong}"
                    )
                result.note(f"GODOT_VERSION.txt={build}; project.godot features={declared}")
        ci_md = ROOT / "CI.md"
        if not ci_md.is_file():
            result.error("CI.md 缺失")
        else:
            ci_text = read_text(ci_md)
            if build not in ci_text:
                result.error(f"CI.md 未记录锁定构建 {build}（需与 GODOT_VERSION.txt 一致）")
            pinned = str(policy.get("gdtoolkit_version", "")).strip()
            if pinned and pinned not in ci_text:
                result.error(f"CI.md 未记录固定版本 gdtoolkit {pinned}")
        for doc in policy.get("version_docs", []):
            path = ROOT / doc
            if not path.is_file():
                result.error(f"版本一致性文档缺失: {doc}")
            elif build not in read_text(path):
                result.error(f"{doc} 未记录锁定构建 {build}")
    return result


CHECKS = [(NAME, check)]


if __name__ == "__main__":
    import sys

    from ci_common import main_for_module

    sys.exit(main_for_module(CHECKS))
