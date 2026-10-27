# Runtime Boundaries

- **Status:** Proposed
- **Version:** 0.1

This document owns provisional component responsibilities, language direction, inputs, outputs, and cross-boundary rules. It intentionally separates those responsibilities from deployment packaging, which is described in the [architecture overview](overview.md).

## Responsibility matrix

| Component            | Primary responsibility                                        | Initial language            | Main inputs                            | Main outputs                                                                                                                                             |
| -------------------- | ------------------------------------------------------------- | --------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Simulator            | Generate reproducible synthetic machine telemetry             | Python                      | Configuration, seed, condition         | Contract-compliant telemetry windows and labeled datasets; the current CLI writes local files (see the [simulator specification](../specs/simulator.md)) |
| Edge producer        | Acquire, buffer, timestamp, and publish physical measurements | To be selected              | Sensor readings, device configuration  | MQTT telemetry windows                                                                                                                                   |
| MQTT boundary        | Device-oriented publish/subscribe transport                   | Infrastructure              | Producer messages                      | Gateway deliveries                                                                                                                                       |
| Telemetry gateway    | Validate external messages and enter the internal platform    | Go                          | MQTT messages                          | Valid and invalid event outcomes                                                                                                                         |
| Event stream         | Buffer and distribute internal events                         | Infrastructure              | Gateway and worker events              | Consumer-group deliveries                                                                                                                                |
| Persistence consumer | Store source telemetry and derived records                    | Go or Python, to be decided | Valid events                           | PostgreSQL and ClickHouse records                                                                                                                        |
| Analytics worker     | Normalize windows, calculate features, and infer anomalies    | Python                      | Telemetry events and model artifacts   | Features and anomaly observations                                                                                                                        |
| Workflow service     | Apply alert policy and manage maintenance state               | Go                          | Anomaly observations and user commands | Alerts, work orders, maintenance events                                                                                                                  |
| API                  | Expose product and analytical read models                     | Go                          | Database state and query parameters    | HTTP API responses                                                                                                                                       |
| Dashboard            | Present system state and accept user actions                  | React/TypeScript            | API responses                          | User commands through the API                                                                                                                            |
| Observability stack  | Collect and present logs, metrics, and traces                 | Infrastructure              | Instrumented components                | Operational views                                                                                                                                        |

## Boundary rules

1. A producer must not require downstream components to know whether it is simulated or physical.
2. The telemetry gateway should reject malformed input before expensive analytics work.
3. Signal-processing code should remain independently testable from transport and database code.
4. The API should not expose database-specific details as its product contract.
5. Analytical outputs must identify their source event and calculation or model version.
6. Maintenance workflow state must not be inferred only from the latest model prediction.
7. Cross-boundary communication must use explicit schemas or documented API contracts.
8. A process boundary should be introduced only when it provides meaningful ownership, failure isolation, or scaling behavior.

## Initial process grouping

The initial local grouping is described in the [architecture overview](overview.md). It is intentionally provisional; components may be separated or combined as throughput, failure isolation, and development evidence emerge.

## Contract boundaries

Every cross-boundary exchange must have an owning contract document before its implementation begins. The [specifications index](../specs/README.md) is the registry of those documents. The current producer-facing contract is the [telemetry contract](../specs/telemetry-contract.md); internal event, analytical, workflow, and API contracts should be added there as their implementation phases become ready.

## What belongs in an ADR

Create an ADR when a change affects one or more of these boundaries or creates a long-lived operational constraint. Examples include selecting the event-stream implementation, changing the serialization format, splitting the Go process, or choosing a model-serving protocol.
