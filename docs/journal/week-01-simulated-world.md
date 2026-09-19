# Week 01 — Simulated Industrial World

- **Status:** Planned
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
- GitHub P01-001 through P01-008

## Planned outcomes

- [ ] Simulator configuration and condition behavior are specified.
- [ ] Reproducibility metadata and fixed-seed behavior are implemented.
- [ ] Motor, vibration, temperature, and RPM generation are implemented.
- [ ] Telemetry serialization and validation are covered by tests.
- [ ] CLI output and ground-truth sidecar are documented.
- [ ] Plots, limitations, and experiment results are recorded.

## Day 1 — Configuration and domain model

### Plan

Implement the configuration model, condition parameters, execution modes, and
motor domain objects from the simulator specification.

### What happened

### What I learned

### Evidence

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

### What I learned

### Evidence

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
