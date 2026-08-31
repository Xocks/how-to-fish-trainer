# Changelog

## 0.3.0 - 2026-08-31

- Publish the Xocks external edition as a standalone Windows executable without installing a mod or replacing game files.
- Consolidate the runtime item catalog and guarded spawning, 360-degree target selection, 60 Hz item/creature ESP, mouse control panel, silent-aim experiments, and collision-aware third-person camera.
- Use the game's native `PlayerLegs -> PlayerHands -> PlayerBody -> IK` presentation data for the local third-person body and restore all rebound fields and enabled states during every shutdown path.
- Ship the release-unique `HowToFishTrainer.Runtime.V030.dll`, bilingual documentation, sanitized diagnostics, and explicit labels for private-room or server-dependent experiments.
- Pass the complete 92-test automated suite and final DLL/EXE/package integrity checks. Automated coverage does not replace live two-client evidence for server acceptance, remote poses, or hitbox behavior.

## 0.3.0rc4.post8 - 2026-08-31

- Replace the hand-written third-person gait with the game's native `PlayerLegs -> PlayerHands -> PlayerBody -> IK` presentation order, driven by the real local movement, held-item, camera, breathing, ground and boat state.
- Remove the cumulative avatar-root position addition that made the body rise while walking or after creature impacts.
- Correct the native IK contract to `ResolveIK(bool)`, initialize each copied solver before use, and fail closed by hiding the body while preserving the shoulder camera if native presentation binding fails.
- Snapshot and restore every rebound presentation field and component enabled state on Home off, death, reconnect, scene change, exception and F10 shutdown.
- Use the release-unique `HowToFishTrainer.Runtime.RC4Hotfix8.dll`. Automated checks do not prove remote-client appearance or hitbox behavior; those still require the requested live and two-client tests.

## 0.3.0rc4.post7 - 2026-08-30

- Fix the post6 attachment false negative where the external Mono name lookup could not enumerate private `IK.ResolveIK()`, causing a supported running game to be shown as still searching.
- Keep the assembly hash, IK fields, hand-transform getters, and the remaining public runtime contract fail-closed; validate the private IK method inside the managed helper and disable only avatar animation if managed reflection cannot resolve it.
- Distinguish a detected-but-blocked process from a process that has not started, so the dashboard no longer reports “searching” after a compatibility rejection.
- Use the release-unique `HowToFishTrainer.Runtime.RC4Hotfix7.dll`; live third-person animation remains pending game validation.

## 0.3.0rc4.post6 - 2026-08-30

- Fix the confirmed static T-pose in post5. Read-only asset/IL analysis showed that this game has no avatar Animator: remote limbs are driven by `PlayerBody`, `PlayerHands`, `PlayerLegs`, and four `IK` solvers whose targets live outside the copied `Character` hierarchy.
- Copy only the four inert IK configurations into the inactive render-only mirror, create local target/pole proxies, then explicitly solve IK after each static bone sync so the result is not overwritten before rendering. No player, networking, collision, rigidbody, or authority script is copied.
- Align hand IK targets to the held item's own `HandTransformsLeft/Right`; use bounded local gait targets for feet and a small body bob so walking, jumping, and held-tool poses are no longer a static T-pose.
- Split low-head pitch from body direction. Normal direction, backwards direction, and high-speed spin remain mutually exclusive, while low-head can now be enabled independently and combined with backwards or spin.
- Report IK count, animation state/frame count, and the independent low-head state. The local mirror is explicitly an IK preview, not proof of what another client renders or of remote hitbox changes.
- Use the release-unique `HowToFishTrainer.Runtime.RC4Hotfix6.dll`; compilation and 91 automated tests pass, but live motion and two-client network appearance remain pending user validation.

## 0.3.0rc4.post5 - 2026-08-30

- Fix the confirmed `NoSource` avatar failure: the game destroys the local owner's `_newCharacter/_oldCharacter` remote presentation during `Player.InitializePlayer`, so post4 could never mirror it after attachment.
- Discover a renderable source in three fail-closed stages: retained character hierarchy, loaded `PlayerBody` prefab template, then the remaining local body hierarchy. Prefer inactive prefab assets over live remote players and retry a missing source at most once per second.
- Force render-only mirror objects onto the camera-visible Default layer and enable copied Mesh/SkinnedMesh renderers, including recovery from owner-hidden and shadows-only source settings.
- Reapply the local player's retained `PlayerSkin` colors and hat/outfit/accessory mesh selections to a prefab-derived mirror, restoring every reflected renderer field immediately afterward.
- Add source-backend, template-candidate, and appearance-application diagnostics and use the unique `HowToFishTrainer.Runtime.RC4Hotfix5.dll`. Compilation and 91 automated tests pass; the local avatar remains explicitly pending the requested live screenshot/diagnostic validation.

## 0.3.0rc4.post4 - 2026-08-30

- Add a render-only local avatar mirror built from the active `PlayerBody._newCharacter/_oldCharacter` hierarchy. It shares meshes and materials, remaps skinned bones, copies blend shapes, and never copies scripts, networking, colliders, rigidbodies, or animators.
- Rebuild and clean up the avatar mirror across character/equipment changes, death, reconnect, scene changes, Home disable, and F10 shutdown; expose source, mesh, bone, bounds, and rebuild diagnostics.
- Restore the two mutually exclusive private-room pose modes: low/backwards and high-speed body spin. The handler is placed before the existing `SendPosRot` subscriber, changes the camera transform only for the original send window, and restores it immediately afterward.
- Replace the fish-first target priority with a shared F9/End target mask for fish, birds, other creatures, and players. Birds are merged from alive and flying manager collections with instance-ID deduplication; players remain off by default and require per-session private-room consent.
- Add player head/bounds/transform target-point fallbacks and nearest-distance selection across enabled categories with the existing ten-percent switching hysteresis.
- Use the release-unique `HowToFishTrainer.Runtime.RC4Hotfix4.dll` identity. Live local-avatar appearance, remote pose/hitbox behavior, and multiplayer player-ballistics acceptance remain explicitly unverified until the requested single/two-client tests are supplied.

## 0.3.0rc4.post3 - 2026-08-30

- Fix the live `post2` failure where `PlayerBody.Head` was roughly 400 metres away from the rendered `CurCam`, teleporting the render camera into an empty part of the world.
- Use the active source camera position as the canonical shoulder pivot; body/head coordinates are diagnostic-only and can no longer move the camera.
- Reject any render-time displacement above 12 metres and report state `-10` instead of rendering an empty scene.
- Re-assert local body renderer visibility immediately before rendering, including `forceRenderingOff`, while preserving every original value for teardown.
- Add head-to-camera offset and local-body renderer counters to the UI and support bundle, and use the unique `HowToFishTrainer.Runtime.RC4Hotfix3.dll` identity.
- Automated tests and DLL compilation still do not claim live third-person success.

## 0.3.0rc4.post2 - 2026-08-30

- Remove the invalid hard dependency on `PlayerCamera.CamTransform` and `PlayerBody.Head`; third person now starts from the active `Player.CurCam` and uses body, renderer, camera, and player-transform pivot fallbacks.
- Apply the shoulder-camera pose only during Unity's final SRP or built-in camera render callbacks, restoring the gameplay camera immediately after rendering so aiming and firing continue to use the original camera state.
- Fall back after 30 focused frames to the game's configured `PlayerDeathCam._deathCam` camera through `Player.SetCurCam`, without calling the death-only enable or orbit methods.
- Restore camera, culling mask, near clip, body/arm renderers, model activity, reticle, and callback subscriptions on every disable, death, scene, shutdown, and exception path.
- Add backend, source-camera, render-count, requested/applied displacement, and restore-reason diagnostics; pause the unverified outbound pose experiment until the base camera is live-tested.
- Use the release-unique `HowToFishTrainer.Runtime.RC4Hotfix2.dll` identity. Automated tests and DLL compilation do not claim live visual success.

## 0.3.0rc4.post1 - 2026-08-30

- Replace the unreliable F8 hotkey-release option with a dedicated key-up hook and record hotkey registration, receipt, and selector suppression in diagnostics.
- Let silent aim acquire a target without holding right mouse, and correct every newly observed local projectile once before optional in-flight steering.
- Move third-person placement to the exact `PlayerCamera.CamTransform` used by the game, expose active/waiting/failed camera states, and fail closed on runtime exceptions.
- Stop resetting the weapon recoil rig every aim frame, preserving the game's ADS/iron-sight presentation while retaining camera recoil compensation and target-aligned firing.
- Use the release-unique `HowToFishTrainer.Runtime.RC4Hotfix1.dll` identity so a running Mono process cannot reuse the defective RC4 helper.

## 0.3.0rc4 - 2026-08-30

- Add a reversible Home third-person shoulder camera with collision shortening, local-body renderer restoration, and configurable distance, height, shoulder side, and sniper reticle visibility.
- Add a per-session private-room pose experiment that substitutes low/back/spin rotation only during the game's existing `SendPosRot` window and restores the local camera before rendering; remote hitbox behavior remains explicitly unverified.
- Add End silent aim with a pre-`Weapon.Update` fire-point correction that preserves the game's original projectile speed and shotgun spread cone.
- Add optional in-flight steering for local-player entity projectiles only, with per-shot target binding, a 180 degrees/second turn cap, obstruction stop, and no additional shooting RPC.
- Add `ThirdPersonSettings`, `PoseExperimentSettings`, `SilentAimMode`, and `ProjectileTrackingState`, new Home/End hotkeys, diagnostics states, cleanup contracts, and the release-unique `HowToFishTrainer.Runtime.RC4.dll` identity.
- Automated tests and helper compilation are not evidence that camera, remote pose/hitbox, or network projectile behavior works in the live game.

## 0.3.0rc2.post2 - 2026-08-29

- Split the runtime catalog into native pickups, hidden `Item` prefabs, safe static visual previews, and diagnostic-only Unity resources.
- Replace raw engine-prefab instantiation with script-free Mesh/Sprite previews that are normalized into the camera view and destroyed when validation fails.
- Report signed managed spawn states correctly and expose request, native/preview creation, renderer-count, and visibility-validation diagnostics.
- Trigger F8 on key release and deduplicate requests for 400ms so one physical press cannot flood spawn calls or logs.
- Add stable-first and rate-limited continuous airborne-target tracking with separate yaw/pitch limits and a 200ms instability grace period.
- Use the release-unique `HowToFishTrainer.Runtime.RC2Hotfix2.dll` identity.

## 0.3.0rc2.post1 - 2026-08-29

- Give the managed helper a release-unique assembly identity so a still-running game cannot silently reuse the older RC1 contract.
- Initialize and validate the managed runtime during attachment, report its exact failure once, and stop repeated hotkey error flooding.
- Export the managed hidden/resource/engine catalog and merge it into F7 with synthetic IDs after the official game registry.
- Make F10 exit explicit inside the synchronous F7 selector and accept the larger synthetic catalog IDs.
- Prefer the packaged trainer's real `dist/logs` session when collecting diagnostics from the checkout.

## 0.3.0rc2 - 2026-08-29

- Change F9 to a 360-degree, world-distance fish-first selector with optional
  all-creature and through-wall modes.
- Compensate both `PlayerCamera` recoil and the weapon recoil rig, then align
  the fire point without changing damage or network projectile messages.
- Refresh ESP projection at up to 60 Hz, stagger occlusion checks, and expose a
  10-36 point font slider.
- Make Insert capture the game's look and mouse fire actions so interacting
  with the panel does not rotate the camera or fire the weapon.
- Add the mouse-driven Spawn tab with official, named, resource `Item`, and
  explicitly local-only engine-object tiers.
- Stop marking every fish as dangerous. Only real quest items and explosives
  require confirmation; `deadplayer` and network actors remain hard blocked.
- Queue all mouse/F7 selections and F8 requests for Unity-main-thread handling,
  and destroy high-risk local clones on scene change or shutdown.

## 0.3.0rc1 - 2026-08-29

### Added

- Add a fail-closed assembly hash, Mono contract, and JIT entry compatibility gate for the updated game assembly.
- Add a managed Unity-main-thread helper for F9 creature/player head aim, F11 item/creature labels, and an Insert mouse panel without installing files into the game directory.
- Add explicit client capability states, partial joined-client health protection, and a private-lobby-only safe `Server.BuyItem` request probe with two-second throttling.

### Fixed

- Permanently block ID 53, `deadplayer`, and prefabs with a `DeadPlayer` component before selection or native spawning.
- Resolve Mono exports from target memory or the attached module path instead of a hard-coded Steam location.
- Serialize every temporary `Player.LateUpdate` patch through one shared lock and validate native prologues before patching.

### Validation

- Compile `HowToFishTrainer.Runtime.dll` against the current read-only game assemblies using the local .NET Framework compiler.
- Add automated coverage for compatibility failure, spawn safety, client cooldowns, aim/ESP control state, and main-thread dispatch.
- Live single-player and two-client validation remains required before creating a `v0.3.0-rc.1` tag.

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
