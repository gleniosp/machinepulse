# Phase 01 — Simulated Industrial World

- **Status:** Planned
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
- **Acceptance criteria:** Motor parameters, operating conditions, severity,
  duration, sampling, seed, and real-time/accelerated behavior are specified;
  synthetic-data limitations are explicit.
- **Tests or evidence:** Accepted simulator specification and configuration examples.
- **Dependencies:** P00-005, P00-007.

### P01-002 — Define simulator reproducibility metadata

- **Outcome:** Every generated run can be reproduced and audited.
- **Acceptance criteria:** A seed produces repeatable output; configuration,
  generator version, code revision, and separate ground truth are recorded.
- **Tests or evidence:** Metadata fixture and repeatability comparison.
- **Dependencies:** P01-001.

### P01-003 — Implement the motor and operating-condition domain model

- **Outcome:** A motor and its three initial operating conditions are represented
  in testable domain logic.
- **Acceptance criteria:** Nominal RPM and sensor groups are configurable;
  normal, imbalance, and overheating have explicit parameterization; unit tests
  cover the domain rules.
- **Tests or evidence:** Unit tests and configuration fixtures.
- **Dependencies:** P01-001.

### P01-004 — Implement sampled vibration generation

- **Outcome:** The simulator generates three-axis vibration windows with
  configurable rotational and condition-specific components.
- **Acceptance criteria:** Declared rate and sample count are honored;
  rotational frequency is derived consistently from RPM; noise and condition
  components are configurable; output is marked synthetic.
- **Tests or evidence:** Deterministic fixtures and exploratory plots.
- **Dependencies:** P01-003.

### P01-005 — Implement temperature and RPM context generation

- **Outcome:** Scalar context accompanies each telemetry window with explicit
  units and documented condition behavior.
- **Acceptance criteria:** Temperature and RPM units are valid; condition
  changes affect context according to documented rules; fixed-seed output is
  reproducible.
- **Tests or evidence:** Unit tests and labeled sample windows.
- **Dependencies:** P01-003.

### P01-006 — Build the telemetry-window serializer and validator

- **Outcome:** Simulator output conforms to `telemetry.v1` and invalid fixtures
  are rejected with useful reasons.
- **Acceptance criteria:** Sample counts, timestamps, identifiers, units, and
  finite numeric values are validated; invalid fixture cases are included.
- **Tests or evidence:** Contract tests and invalid-payload fixtures.
- **Dependencies:** P00-005, P01-004, P01-005.

### P01-007 — Add the simulator CLI and labeled dataset output

- **Outcome:** A documented command generates telemetry and its ground-truth
  sidecar for one or more motors.
- **Acceptance criteria:** Seed, duration, RPM, condition, and output settings
  are configurable; telemetry and sidecar records associate by event ID.
- **Tests or evidence:** CLI help output, example run, and reproducibility manifest.
- **Dependencies:** P01-002, P01-006.

### P01-008 — Add simulator tests, plots, and Week 01 evidence

- **Outcome:** Phase 01 behavior is evaluated and its limitations are recorded.
- **Acceptance criteria:** Unit and contract tests cover all conditions;
  time-domain and frequency-domain plots are produced; Week 01 records commands
  and limitations; the first article draft is evidence-based; the project
  validation commands are executable for the checks that exist in this phase.
- **Tests or evidence:** Test output, plots, journal, article outline/draft, and
  the Phase 01 validation command run.
- **Dependencies:** P01-003 through P01-007.

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

- All Phase 01 acceptance criteria and evidence are linked.
- Reproducibility and contract tests pass.
- Generated telemetry and ground truth are separate and traceable.
- Plots, limitations, and open questions are recorded in the Week 01 journal.
- Follow-up decisions are assigned to the next owning specification or ADR.
