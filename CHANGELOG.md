# Changelog

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
