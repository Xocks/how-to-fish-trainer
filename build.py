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
        "--collect-all",
        "howtofish_cheat",
        "--collect-all",
        "rich",
        "--collect-all",
        "keyboard",
        "--collect-all",
        "pymem",
        "--collect-all",
        "pefile",
        "--collect-all",
        "dnfile",
        "run_trainer.py",
    ]
    print(f"Executing: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("\n[SUCCESS] Build complete! Executable located at: dist/HowToFishTrainer.exe")


if __name__ == "__main__":
    build()
