# Week 01 — Simulated Industrial World

- **Status:** In progress
- **Phase:** 01
- **Theme:** Generate reproducible motor telemetry before hardware exists

## Goal

Implement and evaluate a deterministic simulator that produces contract-
compliant telemetry and separately keyed ground truth for three synthetic
operating conditions.

## Related specifications

- [Simulator behavior](../specs/simulator.md)
- [Telemetry contract](../specs/telemetry-contract.md)

## Related tasks

- [Phase 01 tasks](../tasks/phase-01-simulated-world.md)
- [P01-001 GitHub issue](https://github.com/gleniosp/machinepulse/issues/11)
- [P01-009 GitHub issue](https://github.com/gleniosp/machinepulse/issues/79)
- [P01-010 GitHub issue](https://github.com/gleniosp/machinepulse/issues/83)
- GitHub P01-001 through P01-009

## Planned outcomes

- [x] P01-001 simulator configuration and condition behavior are specified;
  initial signal defaults remain subject to EXP-0001.
- [ ] Reproducibility metadata and fixed-seed behavior are implemented.
- [ ] Motor, vibration, temperature, and RPM generation are implemented.
- [ ] Telemetry serialization and validation are covered by tests.
- [ ] CLI output and ground-truth sidecar are documented.
- [ ] Plots, limitations, and experiment results are recorded.
- [x] The mise/Pixi tooling foundation and repository hooks are installed and
  pass their current checks.
- [ ] Add the pnpm workspace and Vite+ catalog with the first
  JavaScript/TypeScript package.

## Day 1 — Configuration and domain model

### Plan

Specify the configuration model, condition behavior, and execution modes for
P01-001, then implement the accepted domain model.

### What happened

Prepared a simulator specification proposal with configuration fields and an
example, condition equations, window timing, fixed-seed expectations, and
accelerated and real-time behavior. Proposed initial signal values are marked
for evaluation by EXP-0001. Renamed the simulator's scenario-strength setting
to condition intensity and reserved analytical severity for downstream results.
The maintainer chose one scalar temperature and RPM context value per window;
these channels do not need sample arrays at the vibration rate.
Recorded the telemetry event-ID policy in ADR-0001: UUIDv5 for repeatable
simulator windows, with UUIDv7 preferred for physical producers and the
device-local sequence retained for ordering and gap detection.
The specification remains Draft while initial signal defaults await EXP-0001
and midpoint-context semantics await P04-001; no simulator code has been
implemented yet. P01-001 was completed in
[PR #78](https://github.com/gleniosp/machinepulse/pull/78), and its
[issue #11](https://github.com/gleniosp/machinepulse/issues/11) is closed.

### What I learned

Reproducing event timestamps requires the effective configuration to retain
the resolved run start time. Scalar temperature and RPM need explicit window
semantics; the simulator proposal uses midpoint context, pending confirmation
by the signal-processing specification. Real monitoring systems can acquire
vibration, temperature, and speed at different rates, so associating context
with the vibration interval does not require equal-rate sample arrays.

### Evidence

- [Simulator behavior proposal](../specs/simulator.md)
- [Telemetry contract midpoint proposal](../specs/telemetry-contract.md)
- [P01-001 — Specify simulator behavior and configuration](https://github.com/gleniosp/machinepulse/issues/11)
- [PR #78](https://github.com/gleniosp/machinepulse/pull/78)
- [NI sensor guide](https://www.ni.com/en/shop/data-acquisition/sensor-fundamentals/sensors-for-condition-monitoring.html)
- [Rotating electromechanical system dataset](https://doi.org/10.1038/s41597-026-07224-0)

## Day 2 — Signal and context generation

### Plan

Implement sampled three-axis vibration plus temperature and RPM context. Run
the first deterministic fixtures and parameter experiment.

### What happened

### What I learned

### Evidence

## Day 3 — Contract serialization and validation

### Plan

Serialize windows as `telemetry.v1`, validate required fields and numeric
constraints, and add invalid fixtures.

### What happened

### What I learned

### Evidence

## Day 4 — CLI, sidecar, and reproducibility

### Plan

Add the generation command, run manifest, ground-truth sidecar, and repeatability
comparison across normal, imbalance, and overheating runs.

### What happened

Started P01-002 by defining the run-manifest and sidecar metadata shape,
canonical JSON serialization, and the fixed UUIDv5 namespace and tuple encoding
in the simulator specification and ADR-0001. Added the first Python simulator
package with run-manifest and ground-truth record helpers, source revision and
working-tree state capture, and golden fixtures. Replaced manual effective-
configuration validation with strict Pydantic models for run configuration,
manifests, and sidecar records. Added Pydantic as a runtime dependency; deferred
`pydantic-settings` until simulator settings need environment or secret sources.
Split runtime and development
dependencies in `pyproject.toml`, with runtime-only `default` and development
`dev` Pixi environments. Pinned Pixi 0.76.1 in the root mise toolchain, added
Ruff and strict mypy checks, and configured VS Code to use the Pixi development
environment and `src/` import path. Added scoped simulator-agent guidance and
shared pytest fixtures registered through `pytest_plugins`. The current checks
pass: `pixi install --locked`, `pixi run -e dev typecheck`,
`pixi run -e dev test` (13 tests), `pixi run -e dev lint`, and
`pixi run -e dev format-check` from the old `simulator/` location before its
move. The signal generator does not exist yet, so this evidence locks metadata
and event-ID repeatability only;
fixed-seed telemetry-value comparison remains open until generation is
implemented.

### What I learned

The fixed run start time must be present in effective configuration for
timestamps to be reproducible. A source revision alone does not describe
uncommitted edits, so the manifest records working-tree state separately and
allows either value to be explicitly unknown when the runtime cannot determine
it.

### Evidence

- [Run manifest and sidecar fixture tests](../../tools/simulator/tests/test_reproducibility.py)
- [Run manifest fixture](../../tools/simulator/tests/fixtures/run-manifest.v1.json)
- [Ground-truth fixture](../../tools/simulator/tests/fixtures/ground-truth.v1.json)
- [Simulator reproducibility specification](../specs/simulator.md#run-manifest-and-ground-truth-sidecar)
- [ADR-0001 — Telemetry event identifiers](../adr/0001-telemetry-event-identifiers.md)

## Day 5 — Evaluation and communication

### Plan

Run exploratory time-domain and frequency-domain plots, record limitations, and
turn the evidence into the first technical article draft.

### What happened

### What I learned

### Evidence

## Decisions and open questions

- Record final simulator parameter defaults after EXP-0001.
- Record whether the condition components remain useful and non-misleading
  after EXP-0002.
- Record real-time lag behavior and any changes to the simulator specification.

## Blog post outline

See [From Machines to Data: Modeling Industrial Sensor Telemetry Without Hardware](../blog/week-01-simulator-outline.md).

## Weekly review

### Completed

### Deferred

### Changed assumptions

### Next week

Prepare the MQTT and ingestion boundary using the stable simulator contract.

## Tooling follow-up — 2026-09-29 (P01-009 and P01-010)

### What happened

Pinned Go 1.27.1, Node.js 24.21.0, Pixi 0.76.1, and prek 0.5.3 in the root mise
configuration, with mise 2026.8.11 as the minimum supported version. Generated
the root `mise.lock` for the four configured tools. The root `.miserc.toml`
keeps personal global mise tools out of this repository's locked tool
selection.

Moved Pixi workspace ownership to the repository root. The root `pixi.toml` and
`pixi.lock` define shared settings, runtime and development environments, and
simulator tasks. `tools/simulator/pyproject.toml` retains package metadata,
runtime dependencies, build settings, and Python tooling configuration. Removed the
old simulator-local Pixi lockfile and added simulator mise tasks that delegate
to the root Pixi workspace.

Installed both locked Pixi environments. The root `mise run check` passed
format-check, lint, type-check, and all 13 simulator tests. The direct
`mise run test` from the former `simulator/` directory also passed. The
all-files hook run passed trailing-whitespace, end-of-file, merge-conflict,
TOML, and JSON checks; the
YAML hook skipped because no YAML files remain after deferring pnpm setup. The
managed Git hook installed successfully.

The maintainer deferred pnpm workspace creation and installation until a real
JavaScript/TypeScript package is added. No empty pnpm lockfile or placeholder
catalog is retained. At that point, use one named `toolchain` catalog for the
project-local `vite-plus` dependency, with its version specified in the catalog
from the start.

### Evidence

- `mise install --locked`
- `mise run setup`
- `mise exec -- pixi install --locked`
- `mise run check` — 13 tests passed; formatting, lint, and type checks passed.
- `mise run hooks:install`
- `mise run hooks:check` — all configured hooks passed in an isolated staged
  checkout snapshot; YAML was skipped because there are no YAML files.
- `mise run test` from the former `simulator/` directory — 13 tests passed.
- [Developer tooling baseline](../developer-tooling.md)
- [P01-009 and P01-010 task records](../tasks/phase-01-simulated-world.md)

## Tooling refinement — 2026-09-29

Organized the simulator under `tools/simulator` as an engineering telemetry
generator. It does not represent a user-facing product application or an
independently deployed service. Updated ADR-0002's responsibility-based layout,
root mise task targets, the root Pixi package path, simulator guidance,
documentation links, and VS Code's interpreter/source/test paths.

Removed Go and Node.js pins from the root mise toolchain and kept pnpm
unconfigured. Add them with the first Go or JavaScript/TypeScript project,
respectively. The root mise tool list is now Pixi and prek only. Switched the
prek entry from the explicit GitHub backend to the `prek` registry name, which
resolves to `aqua:j178/prek`.

Moved simulator task definitions into `tools/simulator/mise.toml`, with
project-prefixed root aliases for direct access. Pixi supports task
tables in `pyproject.toml`, but task definitions belong to the manifest Pixi
loads; a nested package manifest does not add tasks to the root workspace. The
project aliases run native commands against the root Pixi manifest and
lockfile, preserving the shared environment.

Added scoped local prek hooks: simulator changes run
`mise run simulator:check`, and Pixi or simulator package metadata changes
verify the root lockfile. The
built-in hooks check path portability, large files, whitespace, file endings,
merge markers, and supported structured data. The future Vite+ package will
use one named pnpm catalog from its first package manifest.

Made root `mise run setup` the local bootstrap: it installs the locked mise
tools, the root Pixi development environment, and the Git hook in order. Added
that entry point and the available validation command to the public README; the
developer tooling baseline remains the detailed owner of setup and tool policy.

### Evidence

- `mise registry prek` — resolves to `aqua:j178/prek`.
- `mise lock` — processed Pixi and prek, pruning the old GitHub prek backend,
  Go, and Node entries.
- `mise install --locked` — selected only Pixi and prek.
- `mise run setup` — completed all three setup steps; tools were already
  installed and the Pixi development environment and Git hook were configured.
- `pixi lock --manifest-path pixi.toml` — updated the editable simulator path.
- `mise run simulator:setup` — installed the locked Pixi development
  environment through the root task alias.
- `mise run check` — format, lint, type checks, and all 13 simulator tests
  passed before and after the hook configuration update; the root check now
  also verifies the Pixi lockfile.
- `mise run pixi:lock-check` — confirmed the root Pixi lockfile is current.
- `mise run hooks:check` — built-in hooks passed. The current unstaged directory
  move leaves old `simulator/` paths in Git's index, so the new path-filtered
  local hooks skipped; `mise run simulator:check` and
  `mise run pixi:lock-check` passed independently.
