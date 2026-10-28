"""Shared helpers for the local CI gates.

All gates live in ``tools/ci`` and are imported by ``run_local.py``.  Each
gate module exposes ``CHECKS``: a list of ``(name, callable)`` pairs where the
callable returns a :class:`Result`.  Standalone execution is supported through
``python tools/ci/<gate>.py``.

The configuration lives in ``ci/policy.json`` and is compared with the frozen
baseline in ``ci/baseline_snapshot.json`` by the tightening gate.  No gate may
write to source directories; the only writes performed by this toolchain are
the baseline snapshot (explicitly human approved) and optional evidence logs
inside the system temporary directory.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

ROOT = Path(__file__).resolve().parents[2]
CI_DIR = ROOT / "ci"
POLICY_PATH = CI_DIR / "policy.json"
BASELINE_PATH = CI_DIR / "baseline_snapshot.json"

# Directories that never contain project source we gate on.
EXCLUDED_DIRS = {
    ".git",
    ".godot",
    ".ci-venv",
    "__pycache__",
    ".dsh-rollback",
    ".svn",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp", ".log"}
TEXT_SUFFIXES = {
    ".gd",
    ".tscn",
    ".tres",
    ".godot",
    ".cfg",
    ".md",
    ".json",
    ".yml",
    ".yaml",
    ".py",
    ".txt",
    ".sh",
    ".import",
    ".gdignore",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".csv",
}

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


@dataclass
class Result:
    """Outcome of a single CI gate."""

    name: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(str(message))

    def warn(self, message: str) -> None:
        self.warnings.append(str(message))

    def note(self, message: str) -> None:
        self.notes.append(str(message))


def fail(module: str, message: str) -> Result:
    """Build an immediate failure result (used for missing prerequisites)."""
    result = Result(name=module)
    result.error(message)
    return result


def load_policy() -> dict:
    if not POLICY_PATH.is_file():
        raise FileNotFoundError(f"missing CI policy file: {relative(POLICY_PATH)}")
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def iter_project_files(suffixes: Iterable[str] | None = None) -> Iterator[Path]:
    """Yield project files, skipping caches, virtualenvs and git metadata."""
    wanted = {suffix.lower() for suffix in suffixes} if suffixes else None
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        for name in sorted(files):
            path = Path(base) / name
            if path.suffix.lower() in EXCLUDED_SUFFIXES and path.suffix.lower() != ".log":
                continue
            if wanted is not None and path.suffix.lower() not in wanted:
                continue
            yield path


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text or "")


def excerpt(text: str, max_lines: int = 20, max_chars: int = 4000) -> str:
    """Return a compact, ANSI-free excerpt suitable for a failure message."""
    cleaned = strip_ansi(text or "").replace("\r\n", "\n").strip()
    lines = [line for line in cleaned.splitlines() if line.strip()]
    trimmed = lines[:max_lines]
    if len(lines) > max_lines:
        trimmed.append(f"... ({len(lines) - max_lines} more lines)")
    joined = "\n".join(trimmed)
    if len(joined) > max_chars:
        joined = joined[:max_chars] + "..."
    return joined


def run(
    command: list[str],
    cwd: Path = ROOT,
    timeout: float | None = 300,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Run a command with captured UTF-8 output."""
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [str(part) for part in command],
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        env=env,
    )


def sha256_bytes(payload: bytes) -> str:
    import hashlib

    return hashlib.sha256(payload).hexdigest()


def count_lines(text: str) -> int:
    return len(text.splitlines())


def resolve_godot(policy: dict | None = None) -> tuple[str | None, list[str]]:
    """Locate the Godot binary.

    Order is fixed by the policy: ``$env:GODOT``, the pinned Windows console
    executable, the non-console fallback and finally entries on ``PATH``.
    """
    policy = policy or load_policy()
    candidates = policy.get(
        "godot_candidates",
        [
            "$GODOT",
            r"D:\app_finish\Godot\Godot_v4.7.2-stable_win64_console.exe",
            r"D:\app_finish\Godot\Godot_v4.7.2-stable_win64.exe",
            "godot",
            "godot4",
            "$GODOT_BIN",
        ],
    )
    tried: list[str] = []
    for raw in candidates:
        if raw.startswith("$"):
            name = raw[1:]
            value = os.environ.get(name, "").strip()
            if not value:
                tried.append(f"{raw}=<unset>")
                continue
            tried.append(f"{raw}={value}")
            candidate = Path(value)
            if candidate.is_file():
                return str(candidate), tried
            found = shutil.which(value)
            if found:
                return found, tried
            continue
        tried.append(raw)
        candidate = Path(raw)
        if candidate.is_file():
            return str(candidate), tried
        found = shutil.which(raw)
        if found:
            return found, tried
    return None, tried


def resolve_gdtoolkit_tool(name: str) -> tuple[str | None, str]:
    """Return (path, source) for gdtoolkit console scripts.

    Prefers the project-local ``.ci-venv`` so the pinned version is used on
    developer machines; the GitHub runner installs the same pin globally and
    falls back to ``PATH``.
    """
    venv_bin = ROOT / ".ci-venv" / ("Scripts" if os.name == "nt" else "bin")
    for suffix in (".exe", ""):
        candidate = venv_bin / f"{name}{suffix}"
        if candidate.is_file():
            return str(candidate), relative(candidate)
    found = shutil.which(name)
    if found:
        return found, "PATH"
    return None, "missing"


def tool_version(executable: str) -> str:
    try:
        completed = run([executable, "--version"], timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ""
    output = strip_ansi((completed.stdout or "") + (completed.stderr or "")).strip()
    return output.splitlines()[0].strip() if output else ""


def godot_version(executable: str) -> str:
    try:
        completed = run([executable, "--version"], timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ""
    output = strip_ansi((completed.stdout or "") + (completed.stderr or "")).strip()
    for line in output.splitlines():
        match = re.search(r"\d+\.\d+\.\d+\.[A-Za-z]+\.\w+\.\w+", line)
        if match:
            return match.group(0)
    return output.splitlines()[0].strip() if output else ""


def expected_godot_build(policy: dict | None = None) -> str:
    policy = policy or load_policy()
    version_file = ROOT / policy.get("godot_version_file", "GODOT_VERSION.txt")
    if not version_file.is_file():
        return ""
    return version_file.read_text(encoding="utf-8").strip()


def python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def gdtoolkit_version(policy: dict) -> str:
    return str(policy.get("gdtoolkit_version", ""))


def print_result(result: Result, elapsed: float, verbose: bool = False) -> None:
    """Print one gate line plus its problems."""
    status = "PASS" if result.ok else "FAIL"
    print(f"{status}  {result.name}  ({elapsed:.2f}s)", flush=True)
    for warning in result.warnings:
        print(f"      WARN: {warning}", flush=True)
    for error in result.errors:
        for index, line in enumerate(str(error).splitlines()):
            prefix = "      - " if index == 0 else "        "
            print(f"{prefix}{line}", flush=True)
    if verbose:
        for note in result.notes:
            print(f"      note: {note}", flush=True)


def main_for_module(checks: list[tuple[str, object]]) -> int:
    """Default ``__main__`` behaviour shared by every gate module."""
    import argparse

    parser = argparse.ArgumentParser(description="Run one CI gate.")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    failures = 0
    for name, func in checks:
        import time

        started = time.perf_counter()
        try:
            result = func()  # type: ignore[operator]
        except Exception as exc:  # noqa: BLE001 - gate must not crash silently
            result = Result(name=name, errors=[f"gate crashed: {exc.__class__.__name__}: {exc}"])
        result.name = name
        print_result(result, time.perf_counter() - started, verbose=args.verbose)
        failures += 0 if result.ok else 1
    return 0 if failures == 0 else 1
