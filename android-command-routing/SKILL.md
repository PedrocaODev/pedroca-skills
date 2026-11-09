---
name: android-command-routing
description: adb, android-cli, android run, android emulator, gradlew installDebug, connectedDebugAndroidTest. Use ONLY when Android device, emulator, APK, or app-run workflows may be better served by the android CLI than raw adb or direct Gradle commands.
---

# Android Command Routing

Use this skill only for Android command-line work where the choice between raw
`adb`, raw `./gradlew`, and the higher-level `android` CLI affects speed or
reliability.

Typical triggers:

- `adb ...`
- `android ...`
- emulator provisioning or boot checks
- APK install/run flows
- `./gradlew :app:installDebug`
- `./gradlew :app:connectedDebugAndroidTest`
- tasks whose real goal is device interaction rather than compilation

Do not load it for ordinary Kotlin edits or routine build/test commands like
`assembleDebug`, `lintDebug`, or unit tests unless the task is actually about
device/emulator execution.

## Routing rules

### Prefer the `android` CLI when the task is about

- UI element interactions (`tap`, `text`, `scroll`, `swipe`, `key`) via `android input` using semantic selectors (`text=`, `id=`, `desc=`) instead of raw coordinate taps (`adb shell input tap x y`).
- Headless Compose UI verification and component inspection via `android preview` (`list`, `render`) instead of booting an emulator and deploying an APK.
- Performance profiling and memory investigation via `android profiler` (`systemtrace`, `heapdump`) instead of raw Perfetto CLI or `am dumpheap`.
- Building artifacts via `android build` instead of manual `./gradlew` directory crawling when target references apply.
- Remote physical hardware testing via `android device remote` and desktop mirroring via `android device hub`.
- Field crash and production OOM telemetry via `android signals` (`crashes`, `heaps`).
- Binary artifact inspection and keep-rule optimization audits via `android analyze`.
- Emulator lifecycle management (`start`, `stop`, `list`, `create`) including headless startup (`--headless`).
- Selecting or targeting a running device across commands via `--device=<serial>`.
- Installing and launching APKs via `android run` or `android install`.
- Screenshots (`android screen capture`) and layout inspection (`android layout`).
- Agent-led journey evaluation or multi-step device workflows using `android layout` and `android input`.
- A Gradle command whose real intent is "get this app running on a device".

Examples:

- Prefer `android input tap text="Sign in"` over calculating layout bounds and issuing `adb shell input tap x y`.
- Prefer `android preview render :app` over booting an emulator and assembling an APK just to visually check a Compose layout.
- Prefer `android profiler systemtrace start` over manual Perfetto configuration scripts.
- Prefer `android build :app` over `./gradlew :app:assembleDebug` when target references apply.
- Prefer `android emulator start <name> --headless` over hand-rolled emulator boot orchestration.
- Prefer `android run --apks=...` over low-level install/launch sequences when the goal is simply to run the app.
- Prefer `android layout` / `android screen capture` for UI inspection.

### Prefer raw `adb` when the task is about

- Low-level device operations and diagnostics not covered by `android input` or `android layout`.
- Device log inspection via `adb logcat`.
- Direct `shell`, `am`, `pm`, or file-copy operations (`adb push`, `adb pull`).
- Low-level coordinate input fallbacks when semantic accessibility selectors are not available.
- Commands the `android` CLI does not expose cleanly.

Examples:

- `adb devices`
- `adb logcat -d`
- Targeted low-level shell commands: `adb shell getprop`, `adb shell pm clear <package>`.

### Prefer raw `./gradlew` when the task is about

- Routine build lifecycle tasks not covered by target references: compilation, lint, unit tests, and custom Gradle tasks.
- Static code analysis tasks (`lint`, `detekt`).
- Multi-variant unit testing suites.

Note: While raw `./gradlew` is used for lint, unit tests, and custom tasks, `android build` is preferred for direct artifact builds with target references.

Examples:

- `./gradlew :app:lintDebug`
- `./gradlew :app:testDebugUnitTest`
- `./gradlew check`

## Mixed workflows

Some tasks should combine tools instead of forcing everything through one:

- Render and verify Compose UI fast with `android preview render`, avoiding emulator overhead.
- Build with `android build` (or `./gradlew`), then install and run with `android run`.
- Inspect UI with `android layout` and interact with `android input`, then capture detailed runtime logs with `adb logcat`.
- Profile performance via `android profiler systemtrace`, then pull and analyze traces.
- Use Gradle for unit tests, but prefer `android` helpers for emulator/device orchestration and UI verification.

## Safe workflow

```sh
android --version
android info
adb devices
android build :app
android describe --project_dir=.
android run --device="$SERIAL" --apks=app/build/outputs/apk/debug/app-debug.apk
android layout --device="$SERIAL"
android input --device="$SERIAL" tap text="Continue"
```

- Carry one serial throughout: `android ... --device="$SERIAL"` and `adb -s "$SERIAL" ...`.
- If it is absent/offline, start or reconnect it, or report the blocker; never silently choose another device.
- Use `describe` output when the APK path is unknown.
- Use `android preview render` for fast offline verification of Compose components before committing or deploying.
- Status alone is insufficient: some no-device/runtime errors exit 0, while `android help <command>` exits 1 after printing usage. Validate output/artifacts; prefer parent help when leaf help is rejected.
- The CLI has no journey runner. Journey XML is an agent-evaluation protocol, not an `android` command; drive journeys using `android layout` and `android input`.

## Decision heuristic

Ask: "Is the user's actual goal build/lint/unit test verification, offline UI verification, or device/app interaction?"

- If it is offline Compose UI verification, prefer `android preview`.
- If it is direct artifact compilation by reference, prefer `android build`.
- If it is lint, unit tests, or custom build lifecycle logic, prefer `./gradlew`.
- If it is device/app interaction or UI automation, strongly prefer `android` first (`android input`, `android layout`, `android run`).
- If it is performance profiling or Crashlytics triage, prefer `android profiler` and `android signals`.
- If it is a low-level one-off device command or diagnostic stream (`logcat`, `pm clear`), use `adb`.

When choosing raw `adb` or raw Gradle over the `android` CLI in a borderline
case, state the reason briefly.
