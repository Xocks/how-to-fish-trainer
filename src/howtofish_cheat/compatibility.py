"""Fail-closed compatibility checks for supported How to Fish assemblies."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Optional


RC8_ASSEMBLY_SHA256 = (
    "FA8C6F47874E69FE07B9C978F35CC05372DF2BDD3535DE5F5FAC355F999A5762"
)
CURRENT_ASSEMBLY_SHA256 = (
    "0491C7B5286CA37B42D506113A9C7E32E0AD8D9D121C5FE3BE8E67CE9E9D036B"
)

SUPPORTED_ASSEMBLIES = {
    RC8_ASSEMBLY_SHA256: "steam-24911270",
    CURRENT_ASSEMBLY_SHA256: "steam-2026-08-28",
}


@dataclass(frozen=True)
class CompatibilityReport:
    compatible: bool
    assembly_path: str = ""
    assembly_sha256: str = ""
    build_label: str = "unknown"
    checks: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return asdict(self)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest().upper()


def locate_managed_directory(pm: object, process_name: str) -> Optional[Path]:
    """Derives the Managed directory from the attached executable module."""
    try:
        import pymem.process

        module = pymem.process.module_from_name(pm.process_handle, process_name)
        if not module:
            return None
        executable = Path(module.filename).resolve()
        data_dir = executable.parent / f"{executable.stem}_Data"
        managed = data_dir / "Managed"
        return managed if managed.is_dir() else None
    except Exception:
        return None


class CompatibilityGate:
    """Validates disk identity and required Mono metadata before patching."""

    REQUIRED_METHODS = (
        ("Assembly-CSharp", "GameInfo", "GetSpawnable", 1),
        ("Assembly-CSharp", "Item", "get_DeadPlayer", 0),
        ("Assembly-CSharp", "Player", "LateUpdate", 0),
        ("Assembly-CSharp", "PlayerAimAssist", "GetRotationDelta", 3),
        ("Assembly-CSharp", "Server", "BuyItem", 6),
        ("Assembly-CSharp", "PlayerCamera", "ToggleMouse", 1),
        (
            "Assembly-CSharp",
            "PlayerToolMovement",
            "ResetSwayRecoilPosRotVel",
            0,
        ),
        ("Assembly-CSharp", "DazedCommands", "UseSpawnCommand", 2),
        ("Assembly-CSharp", "Player", "SetCurCam", 1),
        ("Assembly-CSharp", "Player", "SendPosRot", 0),
        ("Assembly-CSharp", "PlayerSkin", "InitializeOther", 0),
        ("Assembly-CSharp", "PlayerBody", "Awake", 0),
        ("Assembly-CSharp", "PlayerBody", "SetAndApplyPosRots", 0),
        ("Assembly-CSharp", "PlayerHands", "Awake", 0),
        ("Assembly-CSharp", "PlayerHands", "LateUpdate", 0),
        ("Assembly-CSharp", "PlayerLegs", "Awake", 0),
        ("Assembly-CSharp", "PlayerLegs", "Update", 0),
        ("Assembly-CSharp", "IK", "Init", 0),
        ("Assembly-CSharp", "IK", "ResolveIK", 1),
        ("Assembly-CSharp", "Item", "get_HandTransformsRight", 0),
        ("Assembly-CSharp", "Item", "get_HandTransformsLeft", 0),
    )
    REQUIRED_FIELDS = (
        ("Assembly-CSharp", "Player", "LocalPlayer"),
        ("Assembly-CSharp", "Player", "_playerSkin"),
        ("Assembly-CSharp", "Player", "_other"),
        ("Assembly-CSharp", "PlayerManager", "OtherPlayers"),
        ("Assembly-CSharp", "Creature", "_headPos"),
        ("Assembly-CSharp", "PlayerBody", "_head"),
        ("Assembly-CSharp", "PlayerBody", "_newCharacter"),
        ("Assembly-CSharp", "PlayerBody", "_oldCharacter"),
        ("Assembly-CSharp", "PlayerBody", "_isOldModel"),
        ("Assembly-CSharp", "PlayerBody", "_lowerBody"),
        ("Assembly-CSharp", "PlayerBody", "_eyes"),
        ("Assembly-CSharp", "PlayerHands", "_handBoneRight"),
        ("Assembly-CSharp", "PlayerHands", "_handBoneLeft"),
        ("Assembly-CSharp", "PlayerHands", "_fingerTransformsRight"),
        ("Assembly-CSharp", "PlayerHands", "_fingerTransformsLeft"),
        ("Assembly-CSharp", "PlayerLegs", "_legTargets"),
        ("Assembly-CSharp", "PlayerLegs", "_ikPoles"),
        ("Assembly-CSharp", "PlayerLegs", "_footModels"),
        ("Assembly-CSharp", "OtherPlayer", "_transform"),
        ("Assembly-CSharp", "OtherPlayer", "_camProxy"),
        ("Assembly-CSharp", "OtherPlayer", "_grounded"),
        ("Assembly-CSharp", "OtherPlayer", "<Velocity>k__BackingField"),
        ("Assembly-CSharp", "OtherPlayer", "<FlatVelocity>k__BackingField"),
        ("Assembly-CSharp", "OtherPlayer", "<FlatLocalVelocity>k__BackingField"),
        ("Assembly-CSharp", "OtherPlayer", "<VelMag>k__BackingField"),
        ("Assembly-CSharp", "OtherPlayer", "<OnBoat>k__BackingField"),
        ("Assembly-CSharp", "PlayerSkin", "_bodyRenderer"),
        ("Assembly-CSharp", "PlayerSkin", "_outfitRenderer"),
        ("Assembly-CSharp", "PlayerSkin", "_hatRenderer"),
        ("Assembly-CSharp", "PlayerSkin", "_accessoryRenderer"),
        ("Assembly-CSharp", "IK", "_chainLength"),
        ("Assembly-CSharp", "IK", "_pole"),
        ("Assembly-CSharp", "BirdManager", "_flyingBirds"),
        ("Assembly-CSharp", "PlayerCamera", "_rot"),
        ("Assembly-CSharp", "PlayerCamera", "_recoilCur"),
        ("Assembly-CSharp", "PlayerCamera", "_recoilTar"),
        ("Assembly-CSharp", "PlayerCamera", "_rawLookInput"),
        ("Assembly-CSharp", "GameInfo", "_nameToSpawnable"),
    )

    def __init__(self, supported_hashes: Optional[dict[str, str]] = None):
        self.supported_hashes = supported_hashes or SUPPORTED_ASSEMBLIES

    def inspect_disk(self, assembly_path: Optional[Path]) -> CompatibilityReport:
        if assembly_path is None:
            return CompatibilityReport(False, errors=("assembly_path_not_found",))
        path = Path(assembly_path).resolve()
        if not path.is_file():
            return CompatibilityReport(
                False,
                assembly_path=str(path),
                errors=("assembly_file_not_found",),
            )
        digest = sha256_file(path)
        build_label = self.supported_hashes.get(digest, "unknown")
        if build_label == "unknown":
            return CompatibilityReport(
                False,
                assembly_path=str(path),
                assembly_sha256=digest,
                errors=("unsupported_assembly_hash",),
            )
        return CompatibilityReport(
            True,
            assembly_path=str(path),
            assembly_sha256=digest,
            build_label=build_label,
            checks=("assembly_exists", "assembly_hash_supported"),
        )

    def inspect_runtime(
        self, mono: object, disk_report: CompatibilityReport
    ) -> CompatibilityReport:
        if not disk_report.compatible:
            return disk_report

        checks = list(disk_report.checks)
        errors: list[str] = []
        classes: dict[tuple[str, str], int] = {}

        def class_ptr(assembly: str, name: str) -> int:
            key = (assembly, name)
            if key not in classes:
                classes[key] = mono.find_class(assembly, name)
            return classes[key]

        for assembly, class_name, method_name, param_count in self.REQUIRED_METHODS:
            try:
                if class_name == "GameInfo" and method_name == "GetSpawnable":
                    mono.find_method_by_signature(
                        class_ptr(assembly, class_name),
                        method_name,
                        (mono.MONO_TYPE_U1,),
                    )
                else:
                    mono.find_method(
                        class_ptr(assembly, class_name), method_name, param_count
                    )
                checks.append(f"method:{class_name}.{method_name}/{param_count}")
            except Exception as exc:
                errors.append(
                    f"method:{class_name}.{method_name}/{param_count}:{exc}"
                )

        for assembly, class_name, field_name in self.REQUIRED_FIELDS:
            try:
                mono.get_field_offset(class_ptr(assembly, class_name), field_name)
                checks.append(f"field:{class_name}.{field_name}")
            except Exception as exc:
                errors.append(f"field:{class_name}.{field_name}:{exc}")

        return CompatibilityReport(
            not errors,
            assembly_path=disk_report.assembly_path,
            assembly_sha256=disk_report.assembly_sha256,
            build_label=disk_report.build_label,
            checks=tuple(checks),
            errors=tuple(errors),
        )


def validate_native_entry(pm: object, address: int, min_size: int = 12) -> bytes:
    """Reads a JIT prologue and rejects obviously invalid patch targets."""
    if not address or address < 0x10000:
        raise RuntimeError(f"Invalid native method entry: 0x{int(address or 0):X}")
    prefix = bytes(pm.read_bytes(address, min_size))
    if len(prefix) != min_size or not any(prefix):
        raise RuntimeError(f"Unreadable native method entry: 0x{address:X}")
    if prefix[0] in {0x00, 0xCC}:
        raise RuntimeError(
            f"Unsafe native method prologue at 0x{address:X}: {prefix.hex()}"
        )
    return prefix
