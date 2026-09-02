# Product Scope

- **Status:** Draft
- **Version:** 0.1

This document owns the first meaningful slice of MachinePulse: what version 0.1 includes, excludes, and must demonstrate. The [product requirements](requirements.md) translate this boundary into stable, testable requirement identifiers.

## Version 0.1 in scope

### Asset

- One asset type: a rotating electric motor.
- Configurable nominal RPM.
- A small set of simulator-defined operating conditions.

### Measurements

- Three-axis vibration: X, Y, and Z.
- Temperature in degrees Celsius.
- Rotational speed in revolutions per minute.

### Simulated conditions

- Normal operation.
- Simulated imbalance.
- Simulated overheating.

These conditions are controlled synthetic scenarios. They are not claims that the simulator is an accurate physical model of a particular machine or failure mode.

### Data platform

- A versioned telemetry window contract.
- MQTT as the initial device communication boundary.
- A Kafka-compatible internal event stream.
- PostgreSQL for operational entities and workflow state.
- ClickHouse for telemetry, features, and analytical history.
- Validation, quarantine, deduplication, and replay behavior.

### Analytics

- Window-based time-domain features.
- FFT-based frequency-domain features.
- A rule-based anomaly baseline.
- One initial unsupervised model, expected to be Isolation Forest.
- A product-level health score with documented limitations.

### Maintenance workflow

- Fleet view.
- Asset detail view.
- Alert details with evidence.
- A minimal work-order flow.
- Maintenance-event history.

### Engineering quality

- Unit and integration tests for the core path.
- Reproducible simulator runs.
- Structured logs and metrics.
- Distributed tracing where practical.
- Load-test and failure-recovery documentation.
- Local execution through documented infrastructure.

### Edge integration

- A physical producer added after the simulated path is working.
- The physical producer implements the existing telemetry contract.
- Sensor noise, timing variation, and connectivity behavior are documented.

## Explicitly out of scope for version 0.1

- A validated digital twin or physics-accurate motor model.
- Safety-critical or regulatory diagnostic claims.
- Comprehensive support for pumps, compressors, turbines, or other asset classes.
- Mobile applications.
- Full enterprise identity, billing, and multi-tenant administration.
- A large catalog of fault types.
- Deep-learning model optimization as a primary goal.
- Hardware integration before the software contract and pipeline are stable.
- A language-model assistant as a dependency of the core monitoring workflow.

A maintenance assistant, document retrieval, additional asset types, and more advanced models may be considered after the core release.

## Version 0.1 completion criteria

Version 0.1 is complete when a clean local environment can demonstrate the following flow:

```text
simulated motor
    → MQTT
    → Go gateway
    → internal event stream
    → validated storage
    → signal features
    → anomaly/health result
    → alert
    → dashboard
    → work order
```

The flow must be testable, observable, reproducible, and documented with known limitations.

## Scope-change rule

A proposed feature should enter version 0.1 only if it:

1. supports the core monitoring workflow;
2. teaches an important physical-systems, data, or reliability concept; or
3. is necessary to make the existing system testable, observable, or operable.

Otherwise, it belongs in a later roadmap.
