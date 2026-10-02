# Phase 01 — Simulated Industrial World

- **Status:** In progress
- **Goal:** Produce deterministic, contract-compliant motor telemetry and evidence without physical hardware.
- **Related specifications:** [Simulator behavior](../specs/simulator.md), [Telemetry contract](../specs/telemetry-contract.md)
- **Related tooling:** [Developer tooling baseline](../developer-tooling.md)
- **Related journal entry:** [Week 01 — Simulated industrial world](../journal/week-01-simulated-world.md)

## Objective

When Phase 01 is complete, a clean local environment can generate reproducible
telemetry for normal, imbalance, and overheating scenarios, validate the
telemetry-window contract, and write a separately keyed ground-truth dataset.

## Prerequisites

- P00-005 telemetry contract review and follow-up ownership.
- P00-007 simulator preparation.
- A documented initial toolchain and validation command set, or an explicit
  follow-up from P00-010.

## Tasks

### P01-001 — Specify simulator behavior and configuration

- **Outcome:** Simulator parameters, conditions, execution modes, limitations,
  and reproducibility expectations are normative.
- **Acceptance criteria:**
  - [x] Motor parameters, operating conditions, condition intensity, duration,
    sampling, and seed are specified.
  - [x] Real-time and accelerated execution expectations are explicit.
  - [x] Synthetic-data limitations are documented.
- **Tests or evidence:** [Simulator specification](../specs/simulator.md),
  configuration example, and
  [merged PR #78](https://github.com/gleniosp/machinepulse/pull/78).
- **GitHub issue:** [#11](https://github.com/gleniosp/machinepulse/issues/11) (closed).
- **Dependencies:** P00-005, P00-007.

### P01-002 — Define simulator reproducibility metadata

- **Outcome:** Run metadata and event identities make generated runs traceable
  and replayable.
- **Acceptance criteria:**
  - [x] The validated effective configuration, including seed and resolved
    start time, is recorded with generator version and source revision state.
  - [x] Identical run metadata produces byte-for-byte stable manifest and
    ground-truth sidecar JSON.
  - [x] Ground-truth condition metadata is recorded separately from production
    telemetry.
  - [x] Deterministic UUIDv5 event IDs reproduce from the same run identity
    and sequence.
- **Tests or evidence:** [Reproducibility tests](../../tools/simulator/tests/test_reproducibility.py), Pydantic models in `tools/simulator/src/machinepulse_simulator/models.py`, and golden manifest/sidecar fixtures in `tools/simulator/tests/fixtures/`.
- **GitHub issue:** [#12](https://github.com/gleniosp/machinepulse/issues/12).
- **Dependencies:** P01-001.
- **Deferred verification:** Repeatable vibration values are covered by
  P01-004. Repeatable temperature/RPM context belongs to P01-005, and identical
  full-run output is verified by P01-008 after generation is implemented.

### P01-003 — Implement the motor and operating-condition domain model

- **Outcome:** A configured motor and its three initial operating conditions
  are represented in testable domain logic.
- **Acceptance criteria:**
  - [x] A motor model validates finite, positive nominal RPM and declares all
    required v0.1 sensor groups: three-axis vibration, temperature, and RPM.
    These groups remain required by FR-004 and `telemetry.v1`.
  - [x] Normal, imbalance, and overheating have typed parameterization and
    enforce their intensity rules; vibration amplitude values are non-negative,
    and imbalance peaks and overheating rise scale from their configured values
    at condition intensity `1.0`.
  - [x] Unit tests cover motor limits, required groups, condition parameters,
    intensity rules, and scaling behavior.
- **Tests or evidence:** [Domain model](../../tools/simulator/src/machinepulse_simulator/domain.py), [domain tests](../../tools/simulator/tests/test_domain.py), reproducibility tests, and `mise run simulator:check` (57 tests passed; lint, type check, and formatting passed).
- **GitHub issue:** [#13](https://github.com/gleniosp/machinepulse/issues/13).
- **Dependencies:** P01-001.

### P01-004 — Implement sampled vibration generation

- **Outcome:** The simulator generates three-axis vibration windows with
  configurable rotational and condition-specific components.
- **Acceptance criteria:**
  - [x] Three vibration axes honor the declared rate and sample count.
  - [x] Rotational frequency is derived consistently from RPM.
  - [x] Noise and condition-specific components are configurable.
  - [x] Generated output is marked synthetic.
  - [x] Identical effective configuration, seed, and generator version produce
    identical ordered vibration values.
- **Tests or evidence:** [Vibration generation tests](../../tools/simulator/tests/test_vibration.py), [spectrum tests](../../tools/simulator/tests/test_vibration_spectrum.py), [generator-version fixture](../../tools/simulator/tests/fixtures/vibration-window.v1.json), and [EXP-0001 vibration plots](../experiments/EXP-0001-simulator-parameters.md).
- **GitHub issue:** [#14](https://github.com/gleniosp/machinepulse/issues/14).
- **Dependencies:** P01-003.

### P01-005 — Implement temperature and RPM context generation

- **Outcome:** Scalar context accompanies each telemetry window with explicit
  units and documented condition behavior.
- **Acceptance criteria:**
  - [x] Temperature and RPM values use valid units.
  - [x] Operating-condition changes affect context according to documented
    rules.
  - [x] Output is reproducible under a fixed seed.
- **Tests or evidence:** [Context generation tests](../../tools/simulator/tests/test_context.py), labeled sample windows and [context generator](../../tools/simulator/src/machinepulse_simulator/context.py) in the [Week 01 journal](../journal/week-01-simulated-world.md#p01-005-temperature-and-rpm-context--2026-10-02), and `mise run simulator:check` (74 tests passed; lint, type check, and formatting passed).
- **GitHub issue:** [#15](https://github.com/gleniosp/machinepulse/issues/15).
- **Dependencies:** P01-003.

### P01-006 — Build the telemetry-window serializer and validator

- **Outcome:** Simulator output conforms to `telemetry.v1` and invalid fixtures
  are rejected with useful reasons.
- **Acceptance criteria:**
  - [ ] Simulator output conforms to `telemetry.v1`.
  - [ ] Sample counts, timestamps, identifiers, units, and finite numeric
    values are validated.
  - [ ] `event_id` uses the canonical UUID form.
  - [ ] Invalid fixture cases are included.
- **Tests or evidence:** Contract tests and invalid-payload fixtures.
- **GitHub issue:** [#16](https://github.com/gleniosp/machinepulse/issues/16).
- **Dependencies:** P00-005, P01-004, P01-005.

### P01-007 — Add the simulator CLI and labeled dataset output

- **Outcome:** A documented command generates telemetry and its ground-truth
  sidecar for one or more motors.
- **Acceptance criteria:**
  - [ ] A documented command generates telemetry for one or more motors.
  - [ ] Seed, duration, RPM, condition, and output settings are configurable.
  - [ ] Telemetry and sidecar records associate by event ID.
- **Tests or evidence:** CLI help output, example run, and reproducibility manifest.
- **GitHub issue:** [#17](https://github.com/gleniosp/machinepulse/issues/17).
- **Dependencies:** P01-002, P01-006.

### P01-008 — Add simulator tests, plots, and Week 01 evidence

- **Outcome:** Phase 01 behavior is evaluated and its limitations are recorded.
- **Acceptance criteria:**
  - [ ] Unit and contract tests cover normal and simulated conditions.
  - [ ] Repeated runs with identical effective configuration, seed, and
    generator version produce identical ordered telemetry and sidecar output.
  - [ ] Time-domain and frequency-domain exploratory plots are produced.
  - [ ] Week 01 records commands, results, and limitations.
  - [ ] The first technical article draft is based on evidence.
  - [ ] Project validation commands run for the checks implemented in this
    phase.
- **Tests or evidence:** Test output, plots, journal, article outline/draft, and
  the Phase 01 validation command run.
- **GitHub issue:** [#18](https://github.com/gleniosp/machinepulse/issues/18).
- **Dependencies:** P01-003 through P01-007.

### P01-009 — Add repository hooks for baseline checks

- **GitHub issue:** [#79](https://github.com/gleniosp/machinepulse/issues/79).

- **Outcome:** Contributors can install and run a small, repeatable set of
  repository checks through the pinned mise toolchain.
- **Acceptance criteria:**
  - [x] Pin `prek` in the root `mise.toml`, commit `mise.lock`, and record the
    supported minimum mise version.
  - [x] Add `prek.toml` with native built-in filename, conflict, size,
    whitespace, newline, and structured-data checks. Scope local pre-commit
    hooks so simulator changes run `mise run simulator:check` and
    workspace/package metadata changes verify the root Pixi lock.
  - [x] Add root mise tasks to install the local Git hook and run all configured
    checks across the repository.
  - [x] Document contributor setup and the manual all-files check; make the
    check command reusable by CI.
  - [x] Run the checks across the existing repository and resolve or explicitly
    tune findings so the all-files check passes.
- **Tests or evidence:** `mise install --locked`, the hook installation task,
  and the all-files check from a fresh isolated checkout snapshot; record the
  resulting command output in the Week 01 journal.
- **Dependencies:** P00-010. Coordinate the shared check command with P01-008.
- **Out of scope:** Markdown-specific linting or formatting, third-party hook
  repositories, language-specific hooks, and selecting or introducing a CI
  provider.

### P01-010 — Establish the polyglot workspace and mise task interface

- **Outcome:** The repository has a root Pixi workspace, a pinned mise toolchain,
  the simulator engineering tool under the ADR's `tools/` area, and common root
  tasks that delegate to self-contained project tasks. Go, Node.js, and pnpm are
  added when their projects are introduced. Native package-manager commands
  remain usable within each project.
- **Acceptance criteria:**
  - [x] Update the [developer tooling baseline](../developer-tooling.md) to
    reflect the accepted ADR's workspace roots, native lockfiles, common task
    interface, and Go workspace pattern.
  - [x] Place the simulator under `tools/simulator` as the synthetic telemetry
    generator in the ADR's responsibility-based repository structure.
  - [x] Pin Pixi and prek through the root mise configuration; commit the root
    mise lockfile and document the supported minimum mise version. Defer Go
    until the first Go project and Node.js/pnpm until the first
    JavaScript/TypeScript project.
  - [x] Add a root Pixi workspace with shared settings and dependency specs
    supported by Pixi; preserve simulator package metadata and direct
    dependencies. Keep its project task names in `tools/simulator/mise.toml`;
    those commands use the root Pixi workspace environment and lockfile.
  - [x] Defer Node.js, pnpm, and the root pnpm workspace until the first
    JavaScript/TypeScript project. At that time, add `apps/*` and `packages/*`
    workspace globs, a root lockfile, and one named catalog for Vite+. Each
    applicable package should reference `vite-plus` through the catalog from
    its initial manifest, with shared versions set in the catalog from the
    beginning. Keep package-specific scripts in each package manifest.
  - [x] Configure root and project mise task roots. Root `setup` installs the
    locked tools, Pixi environment, and Git hook; common root verbs delegate to
    project-prefixed tasks, show which projects ran, and fail when a selected
    task fails. Direct simulator tasks use the `simulator:` prefix. Document
    `dev` and `build` as common task names to add when projects define them.
  - [x] Add a Pixi lock-check task that verifies the root Pixi lockfile is
    current.
  - [x] Keep each project's native setup, lint, test, and build commands
    directly executable. Document the Go pattern: root `go.work` when the
    first module is introduced, with module-owned `go.mod` and `go.sum`.
  - [x] Run the locked tool/dependency setup and root checks from an isolated
    checkout, then record command output and limitations in the Week 01
    journal. Defer pnpm installation and lockfile evidence until the first
    JavaScript/TypeScript project is added.
- **Tests or evidence:** Setup and root checks from a fresh isolated checkout
  snapshot, locked Pixi workspace installation, native simulator task runs,
  root mise task runs, and Week 01 journal evidence. Record pnpm workspace
  evidence with the first JavaScript/TypeScript project.
- **GitHub issue:** [#83](https://github.com/gleniosp/machinepulse/issues/83).
- **Dependencies:** P00-010, accepted ADR-0002, and P01-009
  ([#79](https://github.com/gleniosp/machinepulse/issues/79)). Complete before
  further runtime implementation resumes, including P01-003 through P01-008
  and Phase 02.
- **Out of scope:** Implementing the Go gateway, a TypeScript application,
  infrastructure services, Nx, or a custom cross-language dependency graph.
- **Definition of done:** The accepted ADR is reflected in the tooling baseline,
  the current Python workspace entry points work from clean setup, the common
  root checks report failures accurately, and the journal records evidence and
  remaining limitations. pnpm workspace implementation is deferred until the
  first JavaScript/TypeScript project is added.

### P01-011 — Pin the GitHub CLI in the repository toolchain

- **Outcome:** Contributors can use a repository-managed GitHub CLI version for
  issue and pull-request workflows without relying on a global installation.
- **Acceptance criteria:**
  - [x] Add a pinned GitHub CLI tool version to the root mise configuration and
    refresh the committed mise lockfile.
  - [x] Verify the CLI is available through the locked mise environment and
    `gh --version` succeeds after setup.
  - [x] Document that GitHub authentication remains a per-user setup step and
    is not stored in the repository.
- **Tests or evidence:** `mise run setup` completed, installing from the locked
  tool versions and configuring Pixi and the Git hook; `mise exec -- gh
  --version` reported GitHub CLI 2.98.0. Authentication remains per-user and no
  credentials or authentication state were added to the repository.
- **GitHub issue:** [#90](https://github.com/gleniosp/machinepulse/issues/90).
- **Dependencies:** P01-010.
- **Out of scope:** Automating GitHub authentication, changing repository
  permissions, or adding GitHub Actions workflows.
- **Definition of done:** A clean setup installs the pinned GitHub CLI from the
  committed mise lockfile, and its availability and authentication boundary
  are documented.

## Required experiments

- [EXP-0001](../experiments/EXP-0001-simulator-parameters.md): choose useful
  initial window, sampling, noise, and condition parameter ranges.
- [EXP-0002](../experiments/EXP-0002-condition-separation.md): test whether the
  synthetic conditions are distinguishable in exploratory feature and spectral
  views without claiming physical validity.

## Out of scope

- MQTT, gateway, event-stream, database, dashboard, or physical sensor runtime.
- Validated motor physics or safety-critical diagnosis.
- Anomaly model training beyond producing labeled simulator evidence.

## Definition of done

- [ ] All Phase 01 acceptance criteria are checked and their evidence is linked.
- [ ] Reproducibility and contract tests pass.
- [ ] Generated telemetry and ground truth are separate and traceable.
- [ ] Plots, limitations, and open questions are recorded in the Week 01 journal.
- [ ] Follow-up decisions are assigned to the next owning specification or ADR.
