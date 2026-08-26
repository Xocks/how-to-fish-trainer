"""Tests for workspace-local JSONL diagnostics and bundle collection."""

import json
import zipfile

from howtofish_cheat.diagnostics import DiagnosticSession, collect_diagnostics


def test_diagnostics_stay_inside_supplied_root(tmp_path):
    session = DiagnosticSession(root=tmp_path)
    session.record("item_selected", item={"id": 7, "name": "鲨鱼"})

    assert session.path.is_relative_to(tmp_path)
    payload = json.loads(session.path.read_text(encoding="utf-8").strip())
    assert payload["event"] == "item_selected"
    assert payload["data"]["item"]["name"] == "鲨鱼"


def test_collect_bundle_contains_manifest_and_latest_log(tmp_path):
    session = DiagnosticSession(root=tmp_path)
    session.record("spawn_invoked", item={"id": 8})

    bundle_path = collect_diagnostics(root=tmp_path)
    assert bundle_path.is_relative_to(tmp_path)
    assert bundle_path.parent == tmp_path / "test-artifacts"

    with zipfile.ZipFile(bundle_path) as bundle:
        names = bundle.namelist()
        assert "manifest.json" in names
        assert f"logs/{session.path.name}" in names
        manifest = json.loads(bundle.read("manifest.json"))
        assert manifest["included_log"] == session.path.name
        assert "No saves" in manifest["privacy"]
