# Changelog

## 0.2.0rc8 - 2026-08-27

### Fixed

- Recalculate the F7 grid when the terminal is resized, preserving the first
  previously visible item while updating the page count.
- Run the Rich dashboard in the terminal's alternate screen and clear that
  screen after a resize so stale rows from the previous frame do not remain.

### Changed

- Size F7 pages from both terminal dimensions: wide windows use four item
  pairs, narrow windows fall back to three, two, or one, and available height
  determines the number of rows. A 160x40 terminal can show all 85 current
  catalog entries on one page.

### Validation

- Add responsive-grid tests covering window sizes from 160x40 down to 20x10,
  page-anchor preservation, adaptive rendering, and invalid sizes.

## 0.2.0rc7 - 2026-08-27

### Changed

- Replace the wide F7 item table with a compact grid containing four repeated
  `ID / Item` pairs per row (20 items now fit in five rows).
- Keep special-item warnings compact by appending a red `!` to the item name,
  while preserving the existing second-confirmation prompt.

### Validation

- Add selector rendering coverage for the eight-column grid, partial final
  rows, and risk markers.

## 0.2.0rc6 - 2026-08-27

### Fixed

- Stop calling `mono_gchandle_free` during the game session. The RC5 Unity
  crash report mapped the native stack return address exactly to that call in
  the generated main-thread thunk.
- Cache one pinned managed string per spawn key for the lifetime of the game
  process. Retention is bounded by the 85-entry runtime catalog and is reclaimed
  by the OS when the game exits.

### Added

- Add a controlled `spawn_probe` command for one-shot integration testing
  against a user-started local game without the Rich UI or hotkeys.

### Validation

- Live Build 24911270 probes completed for beer (ID 56), knife (ID 63), and
  sniper rifle (ID 70). Each native spawn call returned, the temporary patch
  was restored, the process remained responsive for the observation window,
  and Unity logged no new native crash marker.

## 0.2.0rc5 - 2026-08-27

### Fixed

- Release the pinned spawn-key GC handle inside the Unity main-thread thunk,
  immediately after `DazedCommands.UseSpawnCommand` returns. This removes the
  post-spawn remote-thread call to `mono_gchandle_free` that timed out in the
  RC4 diagnostic and preceded the game process exit.
- Record the GC-handle cleanup route when the main-thread dispatcher is armed.

## 0.2.0rc4 - 2026-08-27

### Fixed

- Add a two-way restoration handshake to the one-shot main-thread dispatcher.
  After spawning, the Unity thread now waits inside the scratch thunk until
  `Player.LateUpdate` has been completely restored, eliminating the race that
  could crash the game shortly after a successfully spawned item appeared.
- Record dispatcher arming, original prologue bytes, and safe release timing in
  the diagnostic log.

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
