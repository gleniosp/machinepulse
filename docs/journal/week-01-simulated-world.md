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
- GitHub P01-001 through P01-009

## Planned outcomes

- [x] P01-001 simulator configuration and condition behavior are specified;
  initial signal defaults remain subject to EXP-0001.
- [ ] Reproducibility metadata and fixed-seed behavior are implemented.
- [ ] Motor, vibration, temperature, and RPM generation are implemented.
- [ ] Telemetry serialization and validation are covered by tests.
- [ ] CLI output and ground-truth sidecar are documented.
- [ ] Plots, limitations, and experiment results are recorded.

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
`pixi run -e dev format-check` from `simulator/`. The signal generator does not
exist yet, so this evidence locks metadata and event-ID repeatability only;
fixed-seed telemetry-value comparison remains open until generation is
implemented.

### What I learned

The fixed run start time must be present in effective configuration for
timestamps to be reproducible. A source revision alone does not describe
uncommitted edits, so the manifest records working-tree state separately and
allows either value to be explicitly unknown when the runtime cannot determine
it.

### Evidence

- [Run manifest and sidecar fixture tests](../../simulator/tests/test_reproducibility.py)
- [Run manifest fixture](../../simulator/tests/fixtures/run-manifest.v1.json)
- [Ground-truth fixture](../../simulator/tests/fixtures/ground-truth.v1.json)
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
