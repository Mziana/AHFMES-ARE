"""
AHFMES WEB_UI — PyInstaller Desktop Executable Builder (ACC-715)

Compiles the AHFMES-ARE Control Center into a standalone desktop executable.
"""

from __future__ import annotations

import os
import subprocess
import sys


def build_executable() -> int:
    print("======================================================================")
    print("  Compiling AHFMES-ControlCenter.exe via PyInstaller (ACC-715)...")
    print("======================================================================")

    # Validate PyInstaller is available
    try:
        import PyInstaller
    except ImportError:
        print("[WARNING] PyInstaller is not installed in current environment.")
        print("Please run: pip install pyinstaller")
        return 1

    # Separator for --add-data: ';' on Windows, ':' on Unix
    sep = ";" if os.name == "nt" else ":"
    data_arg = f"are/web/index.html{sep}are/web"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--name",
        "AHFMES-ControlCenter",
        "--add-data",
        data_arg,
        "--hidden-import",
        "sqlite3",
        "are/web_ui.py",
    ]

    print(f"Executing: {' '.join(cmd)}\n")
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("\n======================================================================")
        print("  [SUCCESS] Build completed!")
        print("  Executable: dist/AHFMES-ControlCenter/AHFMES-ControlCenter.exe")
        print("======================================================================")
    return res.returncode


if __name__ == "__main__":
    sys.exit(build_executable())
