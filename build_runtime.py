"""Build the managed runtime helper without installing a global .NET SDK."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_MANAGED = Path(
    r"D:\SteamLibrary\steamapps\common\How to Fish\How to Fish\How to Fish_Data\Managed"
)
SOURCE = ROOT / "runtime" / "HowToFishTrainer.Runtime" / "TrainerRuntime.cs"
OUTPUT = (
    ROOT
    / "runtime"
    / "HowToFishTrainer.Runtime"
    / "bin"
    / "Release"
    / "HowToFishTrainer.Runtime.dll"
)


def find_csc() -> Path:
    candidates = (
        Path(os.environ.get("WINDIR", r"C:\Windows"))
        / "Microsoft.NET"
        / "Framework64"
        / "v4.0.30319"
        / "csc.exe",
        Path(os.environ.get("WINDIR", r"C:\Windows"))
        / "Microsoft.NET"
        / "Framework"
        / "v4.0.30319"
        / "csc.exe",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(".NET Framework csc.exe was not found.")


def build_runtime(managed_dir: Path = DEFAULT_MANAGED) -> Path:
    managed_dir = Path(managed_dir).resolve()
    references = [
        "mscorlib.dll",
        "System.dll",
        "System.Core.dll",
        "System.Runtime.dll",
        "netstandard.dll",
        "Assembly-CSharp.dll",
        "FishNet.Runtime.dll",
        "UnityEngine.CoreModule.dll",
        "UnityEngine.IMGUIModule.dll",
        "UnityEngine.InputLegacyModule.dll",
        "UnityEngine.PhysicsModule.dll",
        "UnityEngine.TextRenderingModule.dll",
    ]
    missing = [name for name in references if not (managed_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing game assemblies in {managed_dir}: {', '.join(missing)}"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(find_csc()),
        "/nologo",
        "/target:library",
        "/optimize+",
        "/noconfig",
        "/nostdlib+",
        f"/out:{OUTPUT}",
        *[f"/reference:{managed_dir / name}" for name in references],
        str(SOURCE),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    return OUTPUT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--managed-dir",
        type=Path,
        default=Path(os.environ.get("HTF_MANAGED_DIR", DEFAULT_MANAGED)),
    )
    args = parser.parse_args()
    print(build_runtime(args.managed_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
