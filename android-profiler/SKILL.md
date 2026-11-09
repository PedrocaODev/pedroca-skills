---
name: android-profiler
description: 'Records and analyzes Android performance data and diagnoses performance
  bottlenecks across user apps, system apps, and system services, even if the user
  does not explicitly mention profiling or traces. Use when: recording system traces,
  CPU call stacks, Vulkan GPU/DRM memory, or Java/native heap profiles; analyzing
  Perfetto traces for UI jank, frame drops, ANRs, or app startup latency issues; investigating
  CPU bottlenecks, IPC/Binder storms, or thread scheduling stalls; diagnosing battery
  drain, modem power rails, and kernel wake locks; debugging memory pressure, Low
  Memory Kills (LMK), OOMs, leaks, and allocation churn; performing A/B baseline trace
  comparisons to find regressions; executing ad hoc PerfettoSQL queries on Android
  traces.'
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-23'
  keywords:
  - android performance
  - debugging
  - profiling
  - recording
  - trace analysis
  - memory leaks
  - bottleneck
  - jank
  - SQL
---

Your primary role is to figure out what the user wants to do (disambiguation),
find the right instructions for it (workflow discovery), and follow them
step-by-step (following the execution plan). If the request is unclear, work
with the user to finalize the execution plan before proceeding.

`android profiler` is the preferred CLI recording tool for on-device performance data, complemented by `android signals` for production telemetry.

## Prerequisites and Setup

Before executing any workflows, read [`references/env_setup.md`](references/env_setup.md). It defines
what to set `$SKILL_ROOT` to - the anchor every other path in this skill is
written against.

## Intent Disambiguation

Do not guess the user's intent. If the user request is not clear, **ask the
user** what they want to do before proceeding.

## Recording

Use `android profiler` as the preferred CLI recording tool:

- **System Tracing**: `android profiler systemtrace` captures CPU scheduling, thread slices, frame lifecycles, and GPU counters into a Perfetto trace. Subcommands: `prepare`, `start`, `stop`, `capture`.
- **JVM Heap Dumps**: `android profiler heapdump capture --device=<serial>` captures on-demand JVM heap snapshots on devices running API 29+.
- **Session Management**: `android profiler session list`, `status`, and `terminate` inspect and control active recording sessions.

For detailed guidelines, pre-flight checks, or specialized trace configurations, route through [recording/recording_orchestrator](recording/recording_orchestrator.md).

## Analysis

- **Perfetto Trace Analysis**: Route all local trace analysis requests through [analysis/analysis_orchestrator](analysis/analysis_orchestrator.md).
- **Production OOM Telemetry**: Run `android signals heaps list` and `android signals heaps download` to fetch real field OOM heap dump snapshots captured by Crashlytics directly into the analysis workflow.
