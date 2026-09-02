# Product Requirements

- **Status:** Draft
- **Version:** 0.1

This document owns stable high-level functional and non-functional requirement identifiers. The [product scope](scope.md) owns release boundaries; detailed capability behavior belongs in the linked [specifications](../specs/README.md).

## Functional requirements

### Product and simulation

- **FR-001:** The system must represent a rotating motor asset and an associated telemetry producer.
- **FR-002:** The simulator must generate reproducible telemetry when given the same configuration and seed.
- **FR-003:** The simulator must support normal, simulated imbalance, and simulated overheating conditions.
- **FR-004:** The simulator must generate three-axis vibration, temperature, and RPM values with explicit units and sampling metadata.
- **FR-005:** Synthetic ground-truth condition labels must be kept separate from the production telemetry contract.

### Ingestion and data platform

- **FR-006:** A producer must be able to publish telemetry through MQTT.
- **FR-007:** The ingestion boundary must validate telemetry before publishing it to internal processing.
- **FR-008:** Invalid telemetry must be quarantined or rejected with a reason that can be investigated.
- **FR-009:** Valid telemetry must be available to persistence and downstream processing consumers.
- **FR-010:** Processing must tolerate duplicate delivery through an explicit idempotency strategy.
- **FR-011:** The system must support bounded replay or reprocessing of historical telemetry.
- **FR-012:** Operational entities must be persisted separately from high-volume telemetry and analytical data.

### Analytics

- **FR-013:** The system must calculate documented time-domain features from vibration windows.
- **FR-014:** The system must calculate documented frequency-domain features from vibration windows.
- **FR-015:** The system must provide a rule-based anomaly baseline.
- **FR-016:** The system must support one initial unsupervised anomaly-detection model.
- **FR-017:** Analytical results must identify their source data, method, and version.
- **FR-018:** A health score must expose its inputs or evidence rather than presenting unexplained certainty.

### Maintenance workflow and interface

- **FR-019:** Users must be able to inspect fleet-level asset health.
- **FR-020:** Users must be able to inspect an asset’s telemetry trends and derived features.
- **FR-021:** Users must be able to inspect alert evidence and lifecycle state.
- **FR-022:** Users must be able to create and update a minimal work order.
- **FR-023:** Alerts and work orders must remain traceable to their source observations.

### Edge compatibility and operations

- **FR-024:** A later physical edge producer must be able to use the same telemetry contract as the simulator.
- **FR-025:** The system must expose operational signals for ingestion, processing, invalid data, lag, and alerts.

## Non-functional requirements

- **NFR-001 — Reproducibility:** Simulator runs and analytical experiments must record configuration, seed, code version, and relevant dataset version.
- **NFR-002 — Traceability:** Derived data and workflow objects must retain links to their source events.
- **NFR-003 — Idempotency:** Retrying an event must not create uncontrolled duplicate domain objects.
- **NFR-004 — Data quality:** Validation rules must cover malformed structure, invalid numeric values, inconsistent array lengths, duplicates, and ordering anomalies.
- **NFR-005 — Observability:** Important boundaries must expose structured logs, metrics, and useful failure information.
- **NFR-006 — Resilience:** The system must document behavior during broker, consumer, or database interruption.
- **NFR-007 — Local development:** A new contributor should be able to run the initial system locally using documented commands.
- **NFR-008 — Testability:** Core domain logic and integration boundaries must be testable without physical hardware.
- **NFR-009 — Explainability:** Detection results must distinguish measurements, derived features, model scores, and product policy.
- **NFR-010 — Open-source safety:** The repository must not require proprietary data, credentials, or undocumented external services for the core workflow.
- **NFR-011 — Evolution:** Incompatible contract changes must be versioned and documented.
- **NFR-012 — Performance evidence:** Throughput and latency targets should be established through benchmarks instead of invented upfront numbers.

## Requirement traceability

Implementation task files should reference requirement identifiers. Experiments may validate or challenge a requirement, while ADRs explain architectural choices used to satisfy one or more requirements.
