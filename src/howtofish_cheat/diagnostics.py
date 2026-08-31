"""Workspace-local structured diagnostics and support bundle collection."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import threading
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from . import __version__

BASELINE_GAME_BUILD = "2026-08-28"
BASELINE_ASSEMBLY_SHA256 = (
    "0491C7B5286CA37B42D506113A9C7E32E0AD8D9D121C5FE3BE8E67CE9E9D036B"
)


def project_root() -> Path:
    """Returns the checkout or executable directory used for all writes."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _inside_root(root: Path, path: Path) -> Path:
    root = root.resolve()
    path = path.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Refusing to write outside project root: {path}") from exc
    return path


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return repr(value)


class DiagnosticSession:
    """Writes append-only JSONL diagnostics below the checkout root."""

    def __init__(self, root: Optional[Path] = None, enabled: bool = True):
        self.root = (root or project_root()).resolve()
        self.enabled = enabled
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        self.path = _inside_root(
            self.root, self.root / "logs" / f"spawn-{timestamp}-{os.getpid()}.jsonl"
        )
        self._lock = threading.Lock()

    def record(self, event: str, **data: Any) -> None:
        if not self.enabled:
            return
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "trainer_version": __version__,
            "baseline_game_build": BASELINE_GAME_BUILD,
            "baseline_assembly_sha256": BASELINE_ASSEMBLY_SHA256,
            "data": _json_safe(data),
        }
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def sink(self, event: str, data: dict) -> None:
        self.record(event, **data)


def _git_value(root: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return completed.stdout.strip()
    except Exception as exc:
        return f"unavailable: {exc}"


def collect_diagnostics(root: Optional[Path] = None) -> Path:
    """Creates a sanitized support bundle entirely below ``test-artifacts``."""
    root = (root or project_root()).resolve()
    logs_dir = _inside_root(root, root / "logs")
    packaged_logs_dir = _inside_root(root, root / "dist" / "logs")
    output_dir = _inside_root(root, root / "test-artifacts")
    output_dir.mkdir(parents=True, exist_ok=True)

    packaged_log_files = sorted(
        packaged_logs_dir.glob("spawn-*.jsonl")
        if packaged_logs_dir.exists()
        else [],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    checkout_log_files = sorted(
        logs_dir.glob("spawn-*.jsonl") if logs_dir.exists() else [],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    log_files = packaged_log_files or checkout_log_files
    latest_log = log_files[0] if log_files else None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    bundle_path = _inside_root(
        root, output_dir / f"spawn-test-{timestamp}.zip"
    )

    runtime_dll = (
        root
        / "runtime"
        / "HowToFishTrainer.Runtime"
        / "bin"
        / "Release"
        / "HowToFishTrainer.Runtime.V030.dll"
    )
    runtime_sha256 = None
    if runtime_dll.is_file():
        digest = hashlib.sha256()
        with runtime_dll.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        runtime_sha256 = digest.hexdigest().upper()

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "trainer_version": __version__,
        "baseline_game_build": BASELINE_GAME_BUILD,
        "baseline_assembly_sha256": BASELINE_ASSEMBLY_SHA256,
        "git_commit": _git_value(root, "rev-parse", "HEAD"),
        "git_branch": _git_value(root, "branch", "--show-current"),
        "git_status": _git_value(root, "status", "--short"),
        "included_log": latest_log.name if latest_log else None,
        "included_log_source": (
            str(latest_log.relative_to(root)) if latest_log else None
        ),
        "runtime_helper_sha256": runtime_sha256,
        "privacy": "No saves, complete Unity logs, chat, or credentials are included.",
    }

    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
        if latest_log:
            bundle.write(latest_log, arcname=f"logs/{latest_log.name}")

        lastfailed = root / ".pytest_cache" / "v" / "cache" / "lastfailed"
        if lastfailed.is_file():
            bundle.write(lastfailed, arcname="pytest/lastfailed.json")

    return bundle_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="How to Fish trainer diagnostics")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("collect", help="Create a workspace-local support bundle")
    args = parser.parse_args(argv)

    if args.command == "collect":
        print(collect_diagnostics())
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
