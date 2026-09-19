# Simulator Behavior

- **Status:** Draft
- **Version:** 0.1
- **Owner:** Phase 01 implementation
- **Related product requirements:** FR-001 through FR-005, NFR-001, NFR-008, NFR-009, NFR-010
- **Related specifications:** [Telemetry contract](telemetry-contract.md)
- **Related tasks:** [Phase 01 — Simulated industrial world](../tasks/phase-01-simulated-world.md)
- **Related experiments:** [EXP-0001](../experiments/EXP-0001-simulator-parameters.md), [EXP-0002](../experiments/EXP-0002-condition-separation.md)

## Purpose

Define the deterministic simulator that produces contract-compliant telemetry
for one or more rotating electric motors before physical hardware is connected.
The simulator is an engineering tool for testing the telemetry-to-maintenance
path. It is not a validated physical model or a diagnostic authority.

## Scope

The first simulator supports one motor asset type, three vibration axes,
temperature, RPM, and three named conditions: `normal`, `imbalance`, and
`overheating`. It produces telemetry windows and a separate ground-truth
sidecar keyed by event ID.

It does not model a complete motor, a validated fault mechanism, sensor
calibration, hardware timing behavior, or production inference labels.

## Configuration

Each run must define or record:

- asset and device identifiers;
- nominal RPM;
- condition and severity, where severity is normalized to `0.0` through `1.0`;
- window duration and vibration sampling rate;
- total duration or number of windows;
- random seed;
- generator version; and
- execution mode: accelerated or real-time paced.

The initial development defaults are a one-second window, 1,600 Hz vibration
sampling, severity `0.0` for `normal`, and accelerated execution. Defaults are
configuration choices for experiments, not physical truths.

## Behavior

### Determinism

Given the same configuration, seed, generator version, and execution mode, the
simulator must produce the same ordered telemetry values and ground-truth
metadata. Real-time pacing may change wall-clock delivery timing but must not
change generated values.

### Conditions

- `normal` produces a nominal rotational component, configured noise, and
  stable temperature/RPM context.
- `imbalance` adds a configurable condition component related to rotational
  frequency and records severity in the sidecar.
- `overheating` changes temperature context over the run according to a
  documented parameterization while preserving the raw telemetry contract.

The initial condition equations and parameter ranges must be documented in the
implementation and tested for repeatability. They must not be described as
validated industrial fault signatures.

### Window generation

Each window contains equal-length X, Y, and Z vibration arrays and scalar
temperature and RPM context. The simulator increments device-local sequence
numbers and creates stable event IDs for each window. `occurred_at` is producer
event time in UTC. The serialized output must conform to `telemetry.v1`.

### Execution modes

- **Accelerated:** generate windows as quickly as practical for tests and
  datasets while preserving event-time and sequence semantics.
- **Real-time paced:** release windows according to the configured window
  duration, with documented behavior when generation falls behind.

Both modes share the same generation and serialization path.

## Ground-truth sidecar

Ground truth is stored separately from production telemetry and keyed by
`event_id`. Each record includes condition, severity, seed, generator version,
and the run configuration needed to reproduce it. Production inference code
must not receive this sidecar as an input feature.

## Failure behavior

The simulator must reject invalid configuration before generating output,
including non-positive RPM, sampling rate, duration, sample count, or severity
outside the configured range. Serialization and contract validation failures
must identify the event or run that failed. A failed run must not silently emit
partial output without an explicit result or manifest.

## Observability and evidence

Each run should expose or record run ID, configuration, seed, generator version,
code revision, execution mode, window count, elapsed time, and rejected-window
count. Phase 01 evidence includes repeatability checks, contract fixtures,
time-domain and frequency-domain plots, and a statement of synthetic-data
limitations.

## Acceptance criteria

- [ ] Configuration, conditions, severity, duration, sampling, seed, and
  execution mode are specified.
- [ ] A fixed seed and configuration produce repeatable output.
- [ ] Telemetry and ground truth are separate and associated by event ID.
- [ ] Output conforms to `telemetry.v1` and rejects invalid configuration.
- [ ] Synthetic-data limitations are visible in documentation and evidence.

## Open questions

- Which identifier format should the first implementation use?
- Which condition parameters produce useful, non-misleading exploratory plots?
- What real-time lag behavior should be reported when generation falls behind?
- Which window/default choices should be retained after the parameter experiment?
