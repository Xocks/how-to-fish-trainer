"""Controlled one-shot integration probe for a user-started game session."""

from __future__ import annotations

import argparse
import time
from typing import Callable, Optional

import pymem

from .diagnostics import DiagnosticSession
from .features.spawner import ItemSpawnerCheat
from .mono.bridge import MonoBridge
from .mono.patcher import MethodPatcher


def run_spawn_probe(
    item_id: int,
    *,
    process_name: str = "How to Fish.exe",
    wait_seconds: float = 5.0,
    diagnostics: Optional[DiagnosticSession] = None,
    pm_factory: Callable = pymem.Pymem,
    mono_factory: Callable = MonoBridge,
    patcher_factory: Callable = MethodPatcher,
    spawner_factory: Callable = ItemSpawnerCheat,
    sleeper: Callable[[float], None] = time.sleep,
) -> int:
    """Runs exactly one spawn attempt against an already-running local game.

    The probe never launches the game and never writes game files. Its only
    persistent output is the normal workspace-local JSONL diagnostic stream.
    """
    session = diagnostics or DiagnosticSession()
    pm = None
    mono = None
    patcher = None
    spawner = None
    try:
        session.record(
            "probe_started",
            process_name=process_name,
            item_id=item_id,
            wait_seconds=wait_seconds,
        )
        pm = pm_factory(process_name)
        patcher = patcher_factory(pm)
        mono = mono_factory(pm)
        spawner = spawner_factory(
            pm,
            mono,
            patcher,
            event_sink=session.sink,
        )
        if not spawner.prepare():
            session.record("probe_failed", stage="prepare")
            return 2

        spawner.load_catalog()
        item = spawner.select_item(item_id)
        if item is None:
            session.record("probe_failed", stage="select", item_id=item_id)
            return 2

        session.record("probe_item_selected", item=item.to_dict())
        if not spawner.spawn_selected():
            session.record(
                "probe_failed",
                stage="spawn",
                item=item.to_dict(),
                message=spawner.last_action_message,
            )
            return 3

        sleeper(max(0.0, wait_seconds))
        pm.read_bytes(pm.base_address, 2)
        session.record("probe_completed", item=item.to_dict(), process_alive=True)
        return 0
    except Exception as exc:
        session.record("probe_exception", error=str(exc), item_id=item_id)
        return 4
    finally:
        if spawner is not None:
            try:
                spawner.disable()
            except Exception:
                pass
        if patcher is not None:
            try:
                patcher.restore_all()
            except Exception:
                pass
        if mono is not None:
            try:
                mono.close()
            except Exception:
                pass
        if pm is not None:
            try:
                pm.close_process()
            except Exception:
                pass


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one controlled item-spawn probe against an already-running game"
    )
    parser.add_argument("--item-id", type=int, required=True)
    parser.add_argument("--process", default="How to Fish.exe")
    parser.add_argument("--wait-seconds", type=float, default=5.0)
    parser.add_argument(
        "--confirm-live-spawn",
        action="store_true",
        help="Required acknowledgement that the probe modifies the live game process",
    )
    args = parser.parse_args(argv)
    if not 0 <= args.item_id <= 255:
        parser.error("--item-id must be between 0 and 255")
    if not 0 <= args.wait_seconds <= 30:
        parser.error("--wait-seconds must be between 0 and 30")
    if not args.confirm_live_spawn:
        parser.error("--confirm-live-spawn is required")

    result = run_spawn_probe(
        args.item_id,
        process_name=args.process,
        wait_seconds=args.wait_seconds,
    )
    if result == 0:
        print("Spawn probe completed and the game process remained alive.")
    else:
        print(f"Spawn probe failed with result code {result}; inspect D:\\hkhtf\\logs.")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
