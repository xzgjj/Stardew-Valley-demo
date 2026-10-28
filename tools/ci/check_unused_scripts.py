"""Unreferenced script gate: every first-party ``.gd`` must be reachable.

A script counts as referenced when:

* its ``res://scripts/...gd`` path appears in another project file (scene,
  autoload settings, test, docs or CI config), or
* it declares ``class_name`` and that class name is used elsewhere.
"""

from __future__ import annotations

import re

from ci_common import ROOT, Result, TEXT_SUFFIXES, iter_project_files, read_text, relative

NAME = "unused_scripts"
CLASS_NAME_RE = re.compile(r"^\s*class_name\s+([A-Za-z_]\w*)\s*$", re.M)


def check() -> Result:
    result = Result(name=NAME)

    script_root = ROOT / "scripts"
    scripts = sorted(script_root.rglob("*.gd")) if script_root.is_dir() else []
    if not scripts:
        result.error("scripts/ 下未找到任何 .gd 脚本")
        return result

    corpus: list[tuple[str, str]] = []
    for path in iter_project_files():
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            corpus.append((relative(path), read_text(path)))
        except (OSError, UnicodeDecodeError):
            continue

    class_names: dict[str, str] = {}
    for path in scripts:
        match = CLASS_NAME_RE.search(read_text(path))
        if match:
            class_names[relative(path)] = match.group(1)

    unused: list[str] = []
    for path in scripts:
        rel = relative(path)
        resource_path = "res://" + rel
        referenced = False
        for other_rel, text in corpus:
            if other_rel == rel:
                continue
            if resource_path in text:
                referenced = True
                break
        if not referenced and rel in class_names:
            name = class_names[rel]
            pattern = re.compile(rf"\b{re.escape(name)}\b")
            for other_rel, text in corpus:
                if other_rel == rel:
                    continue
                if pattern.search(text):
                    referenced = True
                    break
        if not referenced:
            unused.append(rel)

    for rel in unused:
        result.error(f"脚本未被引用（res:// 引用扫描未命中）: {rel}")
    if unused:
        result.error(
            "请删除孤儿脚本，或让场景/自动加载/其它脚本/测试显式引用它"
        )
    result.note(f"扫描 {len(scripts)} 个 scripts/*.gd，未引用 {len(unused)} 个")
    return result


CHECKS = [(NAME, check)]


if __name__ == "__main__":
    import sys

    from ci_common import main_for_module

    sys.exit(main_for_module(CHECKS))
