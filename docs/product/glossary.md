# Glossary

- **Status:** Draft
- **Version:** 0.1

This glossary owns shared vocabulary that crosses document boundaries. The [domain model](domain-model.md) is the canonical source for entity definitions and relationships; the glossary links to those definitions instead of copying them.

## Domain entities

| Term | Canonical definition |
|---|---|
| Asset | [Domain model — Asset](domain-model.md#asset) |
| Device | [Domain model — Device](domain-model.md#device) |
| Sensor | [Domain model — Sensor](domain-model.md#sensor) |
| Telemetry window | [Domain model — Telemetry window](domain-model.md#telemetry-window) |
| Feature vector | [Domain model — Feature vector](domain-model.md#feature-vector) |
| Anomaly observation | [Domain model — Anomaly observation](domain-model.md#anomaly-observation) |
| Alert | [Domain model — Alert](domain-model.md#alert) |
| Work order | [Domain model — Work order](domain-model.md#work-order) |
| Maintenance event | [Domain model — Maintenance event](domain-model.md#maintenance-event) |

## Shared terms

| Term | Meaning in MachinePulse |
|---|---|
| **Sample** | One value observed for a signal at a point in time. |
| **Event time** | The time at which a producer says the measurement occurred. |
| **Receipt time** | The time at which a platform component received the event. |
| **Sequence number** | A producer-local ordering value used to identify gaps or out-of-order delivery. |
| **Sampling rate** | The number of samples captured per second for a signal. |
| **Operating condition** | A simulator-controlled scenario, such as normal or imbalance; it is not automatically a real fault diagnosis. |
| **Ground truth** | The simulator's reference label for the scenario it generated, used to evaluate analysis results; see [Simulator condition](domain-model.md#simulator-condition). |
| **Condition intensity** | A simulator input from `0.0` to `1.0` that scales a synthetic condition effect; it is ground-truth metadata, not an analytical result. |
| **Analytical severity** | A downstream rating assigned by a documented analysis or alert policy to an observation; it is derived from telemetry and features, not supplied by the simulator. |
| **Health score** | A product-level representation of current condition derived from rules or model outputs; it is not a validated physical measurement. |
| **Quarantine** | Storage or routing for data that cannot safely enter the normal processing path. |
| **Replay** | Reprocessing previously recorded events under explicitly selected execution semantics. |
| **Idempotency** | The property that retrying the same logical event does not cause uncontrolled repeated effects. |
| **Dead-letter queue** | A destination for messages that cannot be processed after the configured retry policy. |
| **Condition monitoring** | Observing asset measurements over time to identify changes relevant to maintenance. |
| **Predictive maintenance** | Maintenance planning informed by observed condition and estimated future risk; MachinePulse does not claim validated failure prediction in version 0.1. |
| **Edge producer** | Software running close to the physical sensor that acquires, buffers, and publishes measurements. |

Capability-specific terms belong in the specification that introduces them. Contract field meanings belong in the [telemetry contract](../specs/telemetry-contract.md), not here.
