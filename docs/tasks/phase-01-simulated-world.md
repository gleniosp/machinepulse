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

- **Outcome:** Every generated run can be reproduced and audited.
- **Acceptance criteria:**
  - [ ] A fixed seed and effective configuration produce repeatable output.
  - [x] Run configuration, generator version, and code revision are recorded.
  - [x] Ground-truth condition metadata is recorded separately from production
    telemetry.
  - [x] Deterministic UUIDv5 event IDs reproduce from the same run identity
    and sequence.
- **Tests or evidence:** [Reproducibility tests](../../simulator/tests/test_reproducibility.py), Pydantic models in `simulator/src/machinepulse_simulator/models.py`, and golden manifest/sidecar fixtures in `simulator/tests/fixtures/`. Fixed-seed telemetry-value repeatability remains pending the signal generator.
- **GitHub issue:** [#12](https://github.com/gleniosp/machinepulse/issues/12).
- **Dependencies:** P01-001.

### P01-003 — Implement the motor and operating-condition domain model

- **Outcome:** A motor and its three initial operating conditions are represented
  in testable domain logic.
- **Acceptance criteria:**
  - [ ] Nominal RPM and sensor groups are configurable.
  - [ ] Normal, imbalance, and overheating have explicit parameterization.
  - [ ] Unit tests cover the domain rules.
- **Tests or evidence:** Unit tests and configuration fixtures.
- **GitHub issue:** [#13](https://github.com/gleniosp/machinepulse/issues/13).
- **Dependencies:** P01-001.

### P01-004 — Implement sampled vibration generation

- **Outcome:** The simulator generates three-axis vibration windows with
  configurable rotational and condition-specific components.
- **Acceptance criteria:**
  - [ ] Three vibration axes honor the declared rate and sample count.
  - [ ] Rotational frequency is derived consistently from RPM.
  - [ ] Noise and condition-specific components are configurable.
  - [ ] Generated output is marked synthetic.
- **Tests or evidence:** Deterministic fixtures and exploratory plots.
- **GitHub issue:** [#14](https://github.com/gleniosp/machinepulse/issues/14).
- **Dependencies:** P01-003.

### P01-005 — Implement temperature and RPM context generation

- **Outcome:** Scalar context accompanies each telemetry window with explicit
  units and documented condition behavior.
- **Acceptance criteria:**
  - [ ] Temperature and RPM values use valid units.
  - [ ] Operating-condition changes affect context according to documented
    rules.
  - [ ] Output is reproducible under a fixed seed.
- **Tests or evidence:** Unit tests and labeled sample windows.
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
  - [ ] Pin `prek` in the root `mise.toml`, commit `mise.lock`, and record the
    supported minimum mise version.
  - [ ] Add `prek.toml` using only prek's native built-in hooks for trailing
    whitespace, end-of-file newlines, merge-conflict markers, and YAML, TOML,
    and JSON syntax checks.
  - [ ] Add root mise tasks to install the local Git hook and run all configured
    checks across the repository.
  - [ ] Document contributor setup and the manual all-files check; make the
    check command reusable by CI.
  - [ ] Run the checks across the existing repository and resolve or explicitly
    tune findings so the all-files check passes.
- **Tests or evidence:** `mise install --locked`, the hook installation task,
  and the all-files check from a clean checkout; record the resulting command
  output in the Week 01 journal.
- **Dependencies:** P00-010. Coordinate the shared check command with P01-008.
- **Out of scope:** Markdown-specific linting or formatting, third-party hook
  repositories, language-specific hooks, and selecting or introducing a CI
  provider.

### P01-010 — Establish the polyglot workspace and mise task interface

- **Outcome:** The repository has root Pixi and pnpm workspaces, a pinned mise
  toolchain, and common root tasks that delegate to self-contained project
  tasks. Native package-manager commands remain usable within each project.
- **Acceptance criteria:**
  - [x] Update the [developer tooling baseline](../developer-tooling.md) to
    reflect the accepted ADR's workspace roots, native lockfiles, common task
    interface, and Go workspace pattern.
  - [ ] Pin Pixi, Node.js, pnpm, prek, and Go through the root mise
    configuration; commit the root mise lockfile and document the supported
    minimum mise version.
  - [ ] Add a root Pixi workspace with shared settings and dependency specs
    supported by Pixi; migrate the simulator into it while preserving its
    package metadata, direct dependencies, development/runtime environments,
    and native Pixi tasks.
  - [ ] Add a root pnpm workspace, shared dependency catalogs, and root
    lockfile. Keep package-specific dependencies and scripts in each package
    manifest, with workspace globs ready for future apps and packages.
  - [ ] Configure root and project mise task roots. Root `setup`, `lint`,
    `test`, and `check` commands delegate to applicable current project tasks,
    show which projects ran, and fail when a selected task fails. Document
    `dev` and `build` as common task names to add when projects define them.
  - [ ] Keep each project's native setup, lint, test, and build commands
    directly executable. Document the Go pattern: root `go.work` when the
    first module is introduced, with module-owned `go.mod` and `go.sum`.
  - [ ] Run the locked tool/dependency setup and root checks from a clean
    checkout, then record command output and limitations in the Week 01
    journal.
- **Tests or evidence:** Clean-checkout `mise install --locked`, locked Pixi
  and pnpm workspace installation, native simulator task runs, root mise task
  runs, and Week 01 journal evidence.
- **GitHub issue:** [#83](https://github.com/gleniosp/machinepulse/issues/83).
- **Dependencies:** P00-010, accepted ADR-0002, and P01-009
  ([#79](https://github.com/gleniosp/machinepulse/issues/79)). Complete before
  further runtime implementation resumes, including P01-003 through P01-008
  and Phase 02.
- **Out of scope:** Implementing the Go gateway, a TypeScript application,
  infrastructure services, Nx, or a custom cross-language dependency graph.
- **Definition of done:** The accepted ADR is reflected in the tooling baseline,
  current Python and pnpm workspace entry points work from clean setup, the
  common root checks report failures accurately, and the journal records
  evidence and remaining limitations.

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
