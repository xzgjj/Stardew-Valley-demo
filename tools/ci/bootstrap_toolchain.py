"""Install the pinned gdtoolkit version into the project-local ``.ci-venv``.

Usage (same command works on Windows and POSIX):

    python -m venv .ci-venv
    .ci-venv/Scripts/python.exe -m pip install gdtoolkit==4.5.0

This helper performs exactly that, reading the pin from ``ci/policy.json``.
"""

from __future__ import annotations

import subprocess
import sys

from ci_common import ROOT, excerpt, gdtoolkit_version, load_policy, run, tool_version

VENV = ROOT / ".ci-venv"


def venv_python() -> str:
    if sys.platform == "win32":
        return str(VENV / "Scripts" / "python.exe")
    return str(VENV / "bin" / "python")


def bootstrap() -> int:
    policy = load_policy()
    pinned = gdtoolkit_version(policy)
    if not pinned:
        print("ci/policy.json 缺少 gdtoolkit_version", file=sys.stderr)
        return 2
    if not VENV.exists():
        print(f"创建虚拟环境: {VENV}", flush=True)
        completed = run([sys.executable, "-m", "venv", str(VENV)], timeout=600)
        if completed.returncode != 0:
            print("创建 .ci-venv 失败:\n" + excerpt(completed.stderr), file=sys.stderr)
            return 1
    python = venv_python()
    print(f"安装 gdtoolkit=={pinned} -> {python}", flush=True)
    completed = run(
        [
            python,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            f"gdtoolkit=={pinned}",
        ],
        timeout=1800,
    )
    if completed.returncode != 0:
        print("pip install 失败:\n" + excerpt(completed.stderr), file=sys.stderr)
        return 1
    gdlint = str(VENV / ("Scripts/gdlint.exe" if sys.platform == "win32" else "bin/gdlint"))
    print(f"完成: {tool_version(gdlint) or 'gdlint（版本未知）'}")
    return 0


if __name__ == "__main__":
    sys.exit(bootstrap())
