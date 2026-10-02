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
- [P01-011 GitHub issue](https://github.com/gleniosp/machinepulse/issues/90)
- [P01-003 GitHub issue](https://github.com/gleniosp/machinepulse/issues/13)
- [P01-004 GitHub issue](https://github.com/gleniosp/machinepulse/issues/14)
- GitHub P01-001 through P01-009

## Planned outcomes

- [x] P01-001 simulator configuration and condition behavior are specified;
  initial signal defaults remain subject to EXP-0001.
- [x] Reproducibility metadata and fixed-seed vibration generation are
  implemented.
- [x] Motor, vibration, temperature, and RPM generation are implemented.
- [ ] Telemetry serialization and validation are covered by tests.
- [ ] CLI output and ground-truth sidecar are documented.
- [ ] Plots, limitations, and experiment results are recorded.
- [x] The mise/Pixi tooling foundation and repository hooks are installed and
  pass their current checks.
- [ ] Deferred follow-up: add the pnpm workspace and Vite+ catalog when the
  first JavaScript/TypeScript package is introduced.

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

Implemented `iter_vibration_windows` as a lazy generator over the run's
configured window count. Each output carries the declared rate, derived sample
count, window duration, `synthetic: true`, and `simulator.v1` generator version.
The three axes use configured peak amplitudes and phases, RPM-derived rotational
frequency, seeded Gaussian noise, and the intensity-scaled imbalance component.
Sample time uses a run-wide index so rotational phase continues across window
boundaries. Sampling configurations that imply fractional sample counts are
rejected before generation. Added unit coverage for sample counts, fractional
sampling rejection, the RPM/frequency relationship, condition scaling,
continuous phase, seed repeatability, and a golden simulator.v1 output fixture.

Ran the vibration slice of EXP-0001 and generated reproducible time/frequency
plots. The setup, measurements, and limitations are recorded in
[EXP-0001](../experiments/EXP-0001-simulator-parameters.md). It remains in
progress for broader sampling/noise comparisons and context-generation
evidence.

### What I learned

Using the global sample index preserves the signal phase when a run is split
into telemetry windows.

Run configuration uses [Pydantic models](../../tools/simulator/src/machinepulse_simulator/models.py)
because those inputs need field and cross-field validation. Generated
vibration windows use frozen dataclasses: the generator builds them from the
already-validated configuration, so they serve as immutable output containers
rather than another input-validation boundary.

The sample-count property uses integer division to return a whole number of
readings. Configuration validation first confirms that
`rate_hz * window_duration_ms` is evenly divisible by 1000, so the integer
division cannot truncate a fractional sample. Sample times in the signal
still use fractional seconds.

### Evidence

- [Vibration generator](../../tools/simulator/src/machinepulse_simulator/vibration.py)
- [Vibration generation tests](../../tools/simulator/tests/test_vibration.py)
- [Spectrum tests](../../tools/simulator/tests/test_vibration_spectrum.py)
- [Generator-version golden fixture](../../tools/simulator/tests/fixtures/vibration-window.v1.json)
- [EXP-0001 vibration results and plots](../experiments/EXP-0001-simulator-parameters.md)
- `mise run simulator:experiment:vibration` — regenerated both EXP-0001 plots and reproduced the six 30 Hz dominant peaks and recorded summaries.
- `mise run hooks:check` — simulator formatting, lint, strict type checking, all 68 tests, repository hooks, and the Pixi lock check passed.
- `mise exec -- pixi run --manifest-path pixi.toml --locked -e dev python -c 'from xml.etree import ElementTree; from pathlib import Path; [ElementTree.parse(path) for path in Path("docs/experiments/artifacts").glob("EXP-0001-vibration-*.svg")]'` — both plot files parsed as XML.

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

## P01-002 scope and verification — 2026-09-30

The maintainer confirmed P01-002 should cover reproducibility metadata and
event identities without absorbing the not-yet-implemented signal and context
generators. Narrowed the task's repeatability acceptance to deterministic
manifest and sidecar serialization; P01-004 owns repeatable vibration values,
P01-005 owns repeatable temperature/RPM context, and P01-008 owns a full-run
comparison once those generators exist. Added an explicit repeated-sidecar
assertion to the reproducibility tests. `mise run simulator:check` passed:
formatting, lint, type checks, and all 13 tests. The local acceptance criteria
are now evidenced; issue #12 remains open until the maintainer-approved PR is
merged.

### Evidence

- [P01-002 GitHub issue](https://github.com/gleniosp/machinepulse/issues/12)
- [Phase 01 task breakdown](../tasks/phase-01-simulated-world.md)
- [Reproducibility tests](../../tools/simulator/tests/test_reproducibility.py)
- `mise run simulator:check` — formatting, lint, type checks, 13 tests passed.

## P01-003 motor and condition domain model — 2026-09-30

Added typed simulator domain models for a motor and the `normal`, `imbalance`,
and `overheating` conditions. The motor validates finite, positive nominal RPM
and declares the required v0.1 groups: three-axis vibration, temperature, and
RPM. Those groups stay required to match FR-004 and the `telemetry.v1`
contract. The condition models enforce zero intensity for normal and positive
intensity through 1.0 for simulated faults. Imbalance peak amplitude and
overheating temperature rise are computed from their configured intensity-1
values. The term means the parameter value at condition intensity `1.0`;
lower intensities scale it linearly. Vibration amplitudes reject negative
values, while phase offsets remain signed. The run configuration constructs
only the selected condition model, so normal and imbalance runs do not need
overheating-only constructor arguments (and vice versa). `EffectiveRunConfig`
exposes these domain views without changing the serialized run-manifest
configuration established by P01-002.

Updated the P01-003 task and issue acceptance wording to reflect the required
v0.1 sensor groups. Whitespace-only identifiers now use a shared Pydantic
`StringConstraints` type, and condition/intensity validation is explicit for
the flattened run config. Cross-field validators keep manifest and ground-truth
metadata aligned with their effective configuration. `mise run simulator:check`
passed: formatting, lint, strict type checking, and all 57 simulator tests.
Amplitude fields reject negative values while phase offsets allow signed finite
values. The condition model is constructed from only the parameters used by the
selected condition; sidecar intensity is finite and within `[0, 1]`, and
sidecar seed is non-negative. Issue #13 remains open until the
maintainer-approved PR is merged.

### Evidence

- [Motor and condition domain models](../../tools/simulator/src/machinepulse_simulator/domain.py)
- [Effective run configuration](../../tools/simulator/src/machinepulse_simulator/models.py)
- [Domain tests](../../tools/simulator/tests/test_domain.py)
- [P01-003 task acceptance](../tasks/phase-01-simulated-world.md)
- [P01-003 GitHub issue](https://github.com/gleniosp/machinepulse/issues/13)
- `mise run simulator:check` — formatting, lint, strict mypy, and 57 tests passed.

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

## GitHub CLI toolchain — 2026-10-02

Pinned GitHub CLI 2.98.0 in the root mise configuration and regenerated the
multi-platform mise lockfile. The developer tooling baseline now directs
contributors to use the mise-managed CLI and authenticate per user; repository
credentials and authentication state remain out of scope.

### Evidence

- `mise lock` — updated the lockfile with checksums and provenance metadata for
  GitHub CLI across the configured platforms.
- `mise run setup` — completed locked tool installation, Pixi development
  environment setup, and Git hook installation.
- `mise exec -- gh --version` — reported GitHub CLI 2.98.0.

## P01-005 temperature and RPM context — 2026-10-02

Added a deterministic context iterator that yields one zero-based context
record per configured run window. Each record carries temperature in degrees
Celsius and rotational speed in RPM, and its index aligns it with the matching
vibration window. Normal and imbalance scenarios retain the configured initial
temperature; overheating applies the configured intensity-scaled rise at each
window midpoint. RPM remains at nominal speed for every condition. Context
generation uses no random values, so the same effective run configuration
produces identical ordered context.

Added coverage for all three conditions, midpoint values, units in the output
field names, ordered window association, repeated generation, and non-finite
calculated temperature. The context implementation and checks follow the
existing simulator specification; no contract or condition rules changed.

These labeled synthetic examples show the generated context values. The
condition and intensity columns are ground-truth labels; they are not fields in
the context records.

| Condition | Intensity | Window index | Temperature (°C) | RPM (rev/min) |
|---|---:|---:|---:|---:|
| normal | 0.0 | 0 | 40.0 | 1800.0 |
| imbalance | 0.7 | 0 | 40.0 | 1800.0 |
| overheating | 0.5 | 0 | 40.625 | 1800.0 |
| overheating | 0.5 | 3 | 44.375 | 1800.0 |

### Evidence

- [Context generator](../../tools/simulator/src/machinepulse_simulator/context.py)
- [Context generation tests](../../tools/simulator/tests/test_context.py)
- Focused run: `pixi run --manifest-path ../../pixi.toml --locked -e dev pytest tests/test_context.py` from `tools/simulator` — 6 passed.
- `mise run simulator:check` — formatting, lint, strict type checks, and all 74 simulator tests passed.

## P01-012 pull-request checks workflow — 2026-10-02

Added a GitHub Actions workflow for pull requests targeting `main`. It uses
read-only repository permissions, checks out without persisting credentials,
installs the pinned mise toolchain from the repository lockfile, prepares the
locked simulator development environment, and runs `mise run hooks:check`.
That command covers all-files repository hooks, simulator checks and tests, and
the Pixi lock validation. The workflow reports pass/fail but does not make its
status a merge requirement; required-check gating is deferred until the project
begins accepting outside contributions.

The workflow uses commit-pinned checkout and mise setup actions. Local YAML
syntax validation and repository checks passed. Passing and failing GitHub
Actions runs remain pending a PR run.

### Evidence

- [Pull-request workflow](../../.github/workflows/pr-checks.yml)
- Pinned action releases: [actions/checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1) and [jdx/mise-action v5.0.1](https://github.com/jdx/mise-action/releases/tag/v5.0.1).
- `mise run hooks:check` — all eligible repository hooks passed, including simulator checks and Pixi lock validation. The all-files YAML hook did not select the new untracked workflow file.
- `mise exec -- prek run check-yaml --files .github/workflows/pr-checks.yml` — passed for the new workflow.
- `git diff --check` — passed.
- Passing and failing GitHub Actions runs remain pending a PR run.
- [P01-012 GitHub issue](https://github.com/gleniosp/machinepulse/issues/93)
