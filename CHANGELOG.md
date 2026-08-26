# Changelog

## 0.2.0rc3 - 2026-08-27

### Fixed

- Dispatch `DazedCommands.UseSpawnCommand` from a one-shot
  `Player.LateUpdate` main-thread gate instead of a remote worker thread.
- Pin the managed spawn-key string until the main-thread call completes.
- Classify the uninitialized prefab catalog using the verified Build 24911270
  resource layout when the non-serialized `Item._type` remains at zero.
- Include per-category totals and the main-thread dispatch route in diagnostics.

## 0.2.0rc2 - 2026-08-27

### Fixed

- Resolve `GameInfo.GetSpawnable(System.Byte)` by its exact Mono parameter
  type instead of accidentally selecting the same-count `System.String`
  overload, which caused F7 catalog scans to return zero items in-game.
- Record the exact catalog lookup signature in diagnostic events.

## 0.2.0rc1 - 2026-08-27

### Added

- Runtime-discovered F7 item catalog with ID input, paging, localization, and risk confirmation.
- F8 native item spawning for single-player and hosts through the game's Unity/FishNet lifecycle.
- Managed Mono string helpers with scratch-buffer and string-length bounds.
- Workspace-local JSONL diagnostics and sanitized support bundle collection.
- Automated coverage for catalog discovery, selector behavior, authority checks, cooldown, diagnostics, and regressions.

### Safety and release status

- Joined clients are blocked from item spawning.
- Quest and unknown items require explicit second confirmation.
- This release candidate has not yet been validated against a running game process. Final `0.2.0` depends on user-provided in-game test results.
