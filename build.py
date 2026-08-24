"""Build single standalone executable using PyInstaller."""

import subprocess
import sys


def build():
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--console",
        "--name",
        "HowToFishTrainer",
        "--paths",
        "src",
        "--optimize",
        "2",
        "--exclude-module",
        "tkinter",
        "--exclude-module",
        "unittest",
        "--exclude-module",
        "doctest",
        "--exclude-module",
        "pydoc",
        "--exclude-module",
        "pygments",
        "--exclude-module",
        "setuptools",
        "--exclude-module",
        "pythonnet",
        "--exclude-module",
        "clr_loader",
        "--exclude-module",
        "dnfile",
        "--exclude-module",
        "multiprocessing",
        "--exclude-module",
        "asyncio",
        "--exclude-module",
        "concurrent",
        "--exclude-module",
        "xml",
        "--exclude-module",
        "xmlrpc",
        "--exclude-module",
        "html",
        "--exclude-module",
        "http",
        "--exclude-module",
        "email",
        "--exclude-module",
        "urllib",
        "--exclude-module",
        "ftplib",
        "--exclude-module",
        "poplib",
        "--exclude-module",
        "imaplib",
        "--exclude-module",
        "smtplib",
        "run_trainer.py",
    ]
    print(f"Executing: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("\n[SUCCESS] Build complete! Executable located at: dist/HowToFishTrainer.exe")


if __name__ == "__main__":
    build()
