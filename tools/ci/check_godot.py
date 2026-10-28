"""Godot engine gate: headless import, regression tests and main scene smoke.

Godot returns exit code 0 even when scripts fail to parse, so the gate also
scans captured output for fatal patterns (``SCRIPT ERROR`` / ``Parse Error`` /
``Failed to load script`` / ``Cannot open file``).  Non-fatal ``ERROR:`` lines
(e.g. resource leak reports at exit) are reported as warnings.

The binary is located in the order fixed by ``ci/policy.json``:
``$env:GODOT`` -> pinned Windows console executable -> non-console fallback ->
``PATH``.
"""

from __future__ import annotations

import os
import re
import subprocess

from ci_common import (
    ROOT,
    Result,
    excerpt,
    expected_godot_build,
    godot_version,
    load_policy,
    read_text,
    relative,
    resolve_godot,
    run,
    strip_ansi,
)

FATAL_PATTERNS = [
    "SCRIPT ERROR",
    "Parse Error",
    "Failed to load script",
    "Cannot open file",
    "Error opening file",
    "Can't open file",
]


def _resolve() -> tuple[str | None, Result, dict]:
    policy = load_policy()
    result = Result()
    executable, tried = resolve_godot(policy)
    if not executable:
        result.error(
            "未找到 Godot 可执行文件。探测顺序: "
            + " -> ".join(tried)
            + "。请设置 $env:GODOT 或把 Godot 4.7.2 加入 PATH。"
        )
    return executable, result, policy


def _scan(result: Result, completed: subprocess.CompletedProcess, label: str) -> str:
    text = strip_ansi((completed.stdout or "") + "\n" + (completed.stderr or ""))
    if completed.returncode != 0:
        result.error(f"Godot {label} 退出码 {completed.returncode}")
    fatal_lines: list[str] = []
    other_errors: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(pattern in stripped for pattern in FATAL_PATTERNS):
            if stripped not in fatal_lines:
                fatal_lines.append(stripped)
        elif stripped.startswith("ERROR:"):
            if stripped not in other_errors:
                other_errors.append(stripped)
    for line in fatal_lines[:12]:
        result.error(f"Godot {label}: {line}")
    if len(fatal_lines) > 12:
        result.error(f"Godot {label}: 其余 {len(fatal_lines) - 12} 条致命输出未逐条列出")
    if other_errors:
        result.warn(
            f"Godot {label}: {len(other_errors)} 条非致命 ERROR（如资源泄漏）: "
            + " | ".join(other_errors[:3])
        )
    if completed.returncode != 0 and not fatal_lines:
        result.error(f"Godot {label} 输出:\n{excerpt(text, 20)}")
    return text


def check_detect() -> Result:
    result = Result()
    executable, probe, policy = _resolve()
    result.errors.extend(probe.errors)
    if not executable:
        return result
    actual = godot_version(executable)
    expected = expected_godot_build(policy)
    if not actual:
        result.error(f"无法读取 Godot 版本: {executable}")
    elif expected and actual != expected:
        result.error(
            f"Godot 版本不一致: 实际 {actual}，GODOT_VERSION.txt 锁定 {expected}"
        )
    result.note(f"Godot: {executable}（{actual or '?'}）")
    return result


def check_import() -> Result:
    result = Result()
    executable, probe, policy = _resolve()
    result.errors.extend(probe.errors)
    if not executable:
        return result
    timeout = float(policy.get("godot_timeouts", {}).get("import", 300))
    command = [executable, "--headless", "--editor", "--path", ".", "--quit"]
    try:
        completed = run(command, cwd=ROOT, timeout=timeout)
    except subprocess.TimeoutExpired:
        result.error(f"Godot 无界面导入超时（>{timeout}s）")
        return result
    _scan(result, completed, "无界面导入")
    result.note(f"导入命令: {' '.join(command)}")
    return result


def check_tests() -> Result:
    result = Result()
    executable, probe, policy = _resolve()
    result.errors.extend(probe.errors)
    if not executable:
        return result
    timeout = float(policy.get("godot_timeouts", {}).get("test", 120))
    tests_dir = ROOT / "tests"
    test_files = sorted(tests_dir.glob("test_*.gd")) if tests_dir.is_dir() else []
    if not test_files:
        result.error("未找到 tests/test_*.gd 回归测试（SceneTree 脚本）")
        return result
    for path in test_files:
        rel = relative(path)
        source = read_text(path)
        if "extends SceneTree" not in source:
            result.error(f"{rel} 未 extends SceneTree，无法用 --script 运行")
            continue
        command = [
            executable,
            "--headless",
            "--path",
            ".",
            "--script",
            "res://" + rel,
        ]
        try:
            completed = run(command, cwd=ROOT, timeout=timeout)
        except subprocess.TimeoutExpired:
            result.error(f"{rel} 运行超时（>{timeout}s）")
            continue
        text = _scan(result, completed, f"回归测试 {rel}")
        if "FAIL:" in text:
            failures = [line.strip() for line in text.splitlines() if "FAIL:" in line]
            for line in failures[:8]:
                result.error(f"{rel}: {line}")
        passed = text.count("PASS:")
        result.note(f"{rel}: {passed} 个 PASS 断言")
    return result


def check_smoke() -> Result:
    result = Result()
    executable, probe, policy = _resolve()
    result.errors.extend(probe.errors)
    if not executable:
        return result
    timeout = float(policy.get("godot_timeouts", {}).get("smoke", 120))

    command = [executable, "--headless", "--path", ".", "--quit-after", "120"]
    try:
        completed = run(command, cwd=ROOT, timeout=timeout)
    except subprocess.TimeoutExpired:
        result.error(f"主场景 smoke 超时（>{timeout}s）")
        completed = None
    if completed is not None:
        _scan(result, completed, "主场景 smoke")
    result.note(f"smoke 命令: {' '.join(command)}")

    # Optional extra smoke scenes (e.g. tests/scene_smoke.tscn) declared in policy.
    for scene in policy.get("godot_smoke_scenes", []):
        scene_file = ROOT / str(scene).removeprefix("res://")
        if not scene_file.is_file():
            result.note(f"可选 smoke 场景不存在，跳过: {scene}")
            continue
        scene_command = [executable, "--headless", "--path", ".", str(scene)]
        try:
            scene_completed = run(scene_command, cwd=ROOT, timeout=timeout)
        except subprocess.TimeoutExpired:
            result.error(f"场景 smoke 超时（>{timeout}s）: {scene}")
            continue
        text = _scan(result, scene_completed, f"场景 smoke {scene}")
        if "FAIL:" in text:
            for line in [row.strip() for row in text.splitlines() if "FAIL:" in row][:8]:
                result.error(f"{scene}: {line}")
        result.note(f"场景 smoke {scene}: {text.count('PASS:')} 个 PASS 断言")
    return result


CHECKS = [
    ("godot_detect", check_detect),
    ("godot_import", check_import),
    ("godot_tests", check_tests),
    ("godot_smoke", check_smoke),
]


if __name__ == "__main__":
    import sys

    from ci_common import main_for_module

    sys.exit(main_for_module(CHECKS))
