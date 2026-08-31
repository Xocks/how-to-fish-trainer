"""Tests for fail-closed game build and runtime contract checks."""

import hashlib
from unittest.mock import MagicMock

import pytest

from howtofish_cheat.compatibility import (
    CompatibilityGate,
    CompatibilityReport,
    validate_native_entry,
)


def test_disk_gate_accepts_known_hash_and_rejects_unknown(tmp_path):
    assembly = tmp_path / "Assembly-CSharp.dll"
    assembly.write_bytes(b"supported-build")
    digest = hashlib.sha256(b"supported-build").hexdigest().upper()
    gate = CompatibilityGate({digest: "test-build"})

    accepted = gate.inspect_disk(assembly)
    assert accepted.compatible is True
    assert accepted.build_label == "test-build"

    assembly.write_bytes(b"different")
    rejected = gate.inspect_disk(assembly)
    assert rejected.compatible is False
    assert rejected.errors == ("unsupported_assembly_hash",)


def test_runtime_gate_fails_closed_when_required_member_is_missing():
    mono = MagicMock()
    mono.find_class.return_value = 0x1000
    mono.find_method.side_effect = RuntimeError("missing method")
    disk = CompatibilityReport(True, assembly_sha256="AA", build_label="test")

    report = CompatibilityGate({"AA": "test"}).inspect_runtime(mono, disk)

    assert report.compatible is False
    assert any("missing method" in error for error in report.errors)


def test_native_entry_validation_rejects_breakpoints_and_zero_addresses():
    pm = MagicMock()
    pm.read_bytes.return_value = b"\xCC" + b"\x90" * 11
    with pytest.raises(RuntimeError, match="Unsafe native"):
        validate_native_entry(pm, 0x100000)
    with pytest.raises(RuntimeError, match="Invalid native"):
        validate_native_entry(pm, 0)


def test_post8_runtime_contract_gates_native_avatar_ik_skin_bird_and_pose_members():
    assert ("Assembly-CSharp", "PlayerBody", "_newCharacter") in CompatibilityGate.REQUIRED_FIELDS
    assert ("Assembly-CSharp", "PlayerBody", "_oldCharacter") in CompatibilityGate.REQUIRED_FIELDS
    assert ("Assembly-CSharp", "Player", "_playerSkin") in CompatibilityGate.REQUIRED_FIELDS
    assert ("Assembly-CSharp", "PlayerSkin", "_bodyRenderer") in CompatibilityGate.REQUIRED_FIELDS
    assert ("Assembly-CSharp", "PlayerSkin", "InitializeOther", 0) in CompatibilityGate.REQUIRED_METHODS
    assert ("Assembly-CSharp", "IK", "_chainLength") in CompatibilityGate.REQUIRED_FIELDS
    # The prior gate looked for the wrong zero-parameter signature. The game's
    # native IK path is ResolveIK(bool), and post8 fails closed on that contract.
    assert ("Assembly-CSharp", "IK", "ResolveIK", 1) in CompatibilityGate.REQUIRED_METHODS
    assert ("Assembly-CSharp", "PlayerBody", "SetAndApplyPosRots", 0) in CompatibilityGate.REQUIRED_METHODS
    assert ("Assembly-CSharp", "PlayerHands", "LateUpdate", 0) in CompatibilityGate.REQUIRED_METHODS
    assert ("Assembly-CSharp", "PlayerLegs", "Update", 0) in CompatibilityGate.REQUIRED_METHODS
    assert ("Assembly-CSharp", "BirdManager", "_flyingBirds") in CompatibilityGate.REQUIRED_FIELDS
    assert ("Assembly-CSharp", "Player", "SendPosRot", 0) in CompatibilityGate.REQUIRED_METHODS
