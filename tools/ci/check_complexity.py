"""Cyclomatic complexity gate based on a lightweight indentation parser.

The gate deliberately avoids a hard dependency on ``gdradon`` (which ships with
gdtoolkit but whose output format changes between releases): GDScript function
bodies are delimited by indentation, and decision points are counted per
function.

Counting rules (per function, base score 1):

* ``if`` / ``elif`` / ``for`` / ``while`` / ``match`` -> +1 each;
* ``match`` branch patterns -> +1 each;
* boolean operators ``and`` / ``or`` -> +1 each (short-circuit paths);
* inline conditionals (``a if cond else b``) are covered by ``if``.

Strings and comments are stripped before counting, so keywords inside text are
not counted.
"""

from __future__ import annotations

import re

from ci_common import ROOT, Result, load_policy, read_text, relative

NAME = "complexity"

FUNC_RE = re.compile(r"^(?P<indent>[ \t]*)func\s+(?P<name>[A-Za-z_]\w*)\s*\(")
KEYWORDS = {
    "if": re.compile(r"(?<![\w.])if\b"),
    "elif": re.compile(r"(?<![\w.])elif\b"),
    "for": re.compile(r"(?<![\w.])for\b"),
    "while": re.compile(r"(?<![\w.])while\b"),
    "match": re.compile(r"(?<![\w.])match\b"),
}
BOOL_OPS = re.compile(r"(?<![\w.])(and|or)\b")
MATCH_IGNORED_BRANCH_PREFIXES = (
    "if ",
    "elif ",
    "else",
    "for ",
    "while ",
    "match ",
    "func ",
    "class ",
)


def _indent_width(prefix: str) -> int:
    return sum(4 if char == "\t" else 1 for char in prefix)


def _leading_whitespace(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" \t"))]


def _strip_code(line: str) -> str:
    """Remove string literals and trailing comments from one source line."""
    output: list[str] = []
    index = 0
    quote = ""
    while index < len(line):
        char = line[index]
        if quote:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in "\"'":
            quote = char
            index += 1
            continue
        if char == "#":
            break
        output.append(char)
        index += 1
    return "".join(output)


def _function_complexity(body: list[str]) -> int:
    score = 1
    match_indents: list[int] = []
    for raw in body:
        code = _strip_code(raw)
        if not code.strip():
            continue
        indent = _indent_width(_leading_whitespace(raw))
        stripped = code.strip()
        while match_indents and indent <= match_indents[-1]:
            match_indents.pop()

        if KEYWORDS["if"].search(code):
            score += 1
        if KEYWORDS["elif"].search(code):
            score += 1
        if KEYWORDS["for"].search(code):
            score += 1
        if KEYWORDS["while"].search(code):
            score += 1
        if KEYWORDS["match"].search(code):
            score += 1
            match_indents.append(indent)
            continue
        score += len(BOOL_OPS.findall(code))
        if (
            match_indents
            and stripped.endswith(":")
            and not stripped.startswith(MATCH_IGNORED_BRANCH_PREFIXES)
        ):
            score += 1
    return score


def _functions(path) -> list[tuple[int, str, list[str]]]:
    lines = read_text(path).splitlines()
    found: list[tuple[int, str, list[str]]] = []
    for index, line in enumerate(lines):
        match = FUNC_RE.match(line)
        if not match:
            continue
        base_indent = _indent_width(match.group("indent"))
        body: list[str] = []
        cursor = index + 1
        while cursor < len(lines):
            raw = lines[cursor]
            if raw.strip():
                indent = _indent_width(_leading_whitespace(raw))
                if indent <= base_indent:
                    break
            body.append(raw)
            cursor += 1
        found.append((index + 1, match.group("name"), body))
    return found


def check() -> Result:
    result = Result(name=NAME)
    policy = load_policy()
    limit = int(policy["max_cyclomatic_complexity"])
    roots = policy.get("gdscript_roots", ["scripts", "tests"])

    paths = []
    for root in roots:
        folder = ROOT / root
        if folder.is_dir():
            paths.extend(sorted(folder.rglob("*.gd")))
    if not paths:
        result.error(f"未找到任何 GDScript（扫描目录: {roots}）")
        return result

    total_functions = 0
    highest = 0
    highest_label = ""
    for path in paths:
        for line_number, name, body in _functions(path):
            total_functions += 1
            score = _function_complexity(body)
            if score > highest:
                highest = score
                highest_label = f"{relative(path)}:{line_number} {name}()"
            if score > limit:
                result.error(
                    f"{relative(path)}:{line_number} {name}() 圈复杂度 {score} > {limit}"
                )
    result.note(
        f"扫描 {len(paths)} 个 .gd / {total_functions} 个函数，"
        f"最高复杂度 {highest}（{highest_label or 'n/a'}），上限 {limit}"
    )
    return result


CHECKS = [(NAME, check)]


if __name__ == "__main__":
    import sys

    from ci_common import main_for_module

    sys.exit(main_for_module(CHECKS))
