# Phase 02 — Telemetry Transport and Ingestion

- **Status:** In progress
- **Goal:** Move contract-compliant telemetry from MQTT through the Go gateway to the internal event stream with validation and observable failure handling.
- **Related specifications:** [Telemetry contract](../specs/telemetry-contract.md), [Ingestion and internal event boundaries](../specs/ingestion.md)
- **Related ADR:** [ADR-0004 — MQTT delivery semantics](../adr/0004-mqtt-delivery-semantics.md) (Accepted)
- **Related journal entry:** [Week 02 — Telemetry transport and ingestion](../journal/week-02-telemetry-ingestion.md)

## Objective

When Phase 02 is locally complete, a local simulator run can publish
`telemetry.v1` windows through MQTT, the Go gateway can validate and route
valid events to the internal stream, invalid messages receive an actionable
terminal outcome, and retries/duplicates/failures are visible. The simulator
and any later physical producer use the same producer contract.

## Prerequisites

- P00-005 telemetry contract review and P01-006 telemetry validation.
- P00-010 developer-tooling baseline, including the Go workspace pattern.
- P02-001 completed; its accepted transport semantics are recorded in the
  [ingestion specification](../specs/ingestion.md) and
  [ADR-0004](../adr/0004-mqtt-delivery-semantics.md).
- P02-002 broker and event-stream selection/configuration recorded where it
  requires a durable architecture choice.

## Tasks

### P02-001 — Specify MQTT topics and ingestion semantics

- **Status:** Complete
- **Outcome:** Device-facing MQTT routing, delivery semantics, clock handling,
  acknowledgement boundaries, and separation from internal event routing are
  specified.
- **Acceptance criteria:**
  - [x] Device-facing topic naming is defined.
  - [x] QoS, reconnect, session, retained-message, acknowledgement, and clock
    behavior are specified.
  - [x] Internal event boundaries are distinguished from MQTT topics.
- **Tests or evidence:** Maintainer approval on 2026-10-15;
  [accepted ingestion specification](../specs/ingestion.md),
  [accepted MQTT ADR](../adr/0004-mqtt-delivery-semantics.md), and official
  [OASIS MQTT 5.0 specification](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html).
- **GitHub issue:** [#19](https://github.com/gleniosp/machinepulse/issues/19).
- **Dependencies:** P00-005, P01-006.
- **Out of scope:** Implementing the broker, gateway, internal event envelope,
  storage, or edge producer.
- **Definition of done:** Maintainer-reviewed topic and delivery semantics are
  recorded in the accepted ingestion specification and ADR; the related issue
  acceptance criteria and evidence links are current.

### P02-002 — Add the local MQTT and event-stream environment

- **Status:** Planned
- **Outcome:** A clean local environment starts the selected MQTT broker and
  Kafka-compatible stream without committed secrets.
- **Acceptance criteria:**
  - [ ] A clean local environment starts the MQTT broker and Kafka-compatible
    stream.
  - [ ] Configuration is documented and does not require committed secrets.
  - [ ] Health checks or readiness behavior are documented.
- **Tests or evidence:** Compose/service startup from the documented clean
  environment, health/readiness output, and configuration review.
- **GitHub issue:** [#20](https://github.com/gleniosp/machinepulse/issues/20).
- **Dependencies:** P00-010, P02-001.
- **Out of scope:** Production deployment, cloud brokers, and external managed
  services.
- **Definition of done:** Local services start repeatably with documented
  readiness checks and no repository credentials.

### P02-003 — Implement the Go MQTT telemetry gateway

- **Status:** Planned
- **Outcome:** The gateway subscribes to the accepted device route, decodes
  messages, preserves producer data, and exposes connection failures.
- **Acceptance criteria:**
  - [ ] The gateway subscribes to the documented device topic.
  - [ ] It decodes messages and preserves producer identity and event time.
  - [ ] It adds receipt metadata without overwriting event metadata.
  - [ ] Connection failures are observable.
- **Tests or evidence:** Gateway unit tests and broker integration evidence for
  connection, subscription, reconnect, and producer metadata preservation.
- **GitHub issue:** [#21](https://github.com/gleniosp/machinepulse/issues/21).
- **Dependencies:** P02-001, P02-002.
- **Out of scope:** Internal event schema, downstream persistence, physical
  hardware acquisition, and product APIs.
- **Definition of done:** The documented gateway path connects, receives, and
  preserves source telemetry with observable connection failure behavior.

### P02-004 — Implement ingress validation and invalid-message handling

- **Status:** Planned
- **Outcome:** External telemetry is validated before internal publication;
  invalid data has an actionable and durable disposition.
- **Acceptance criteria:**
  - [ ] Valid messages continue to internal processing.
  - [ ] Invalid messages receive actionable validation errors.
  - [ ] Invalid payloads are quarantined or routed to the documented invalid
    path.
  - [ ] Validation counters are emitted.
- **Tests or evidence:** Valid/invalid contract fixtures, quarantine evidence,
  and validation-counter output.
- **GitHub issue:** [#22](https://github.com/gleniosp/machinepulse/issues/22).
- **Dependencies:** P01-006, P02-003.
- **Out of scope:** Changing `telemetry.v1` fields, model inference, and
  silently correcting source values.
- **Definition of done:** Valid and invalid messages have tested outcomes and
  invalid reasons remain traceable to the source event or payload.

### P02-005 — Publish versioned internal telemetry events

- **Status:** Planned
- **Outcome:** Valid external telemetry crosses into a separately versioned
  internal event contract.
- **Acceptance criteria:**
  - [ ] Internal event topics and envelope fields are documented.
  - [ ] Source event ID, device, asset, event time, and contract version are
    preserved.
  - [ ] Producer and consumer fixtures cover the initial event version.
- **Tests or evidence:** Internal-event specification, fixture validation, and
  producer/consumer compatibility evidence.
- **GitHub issue:** [#23](https://github.com/gleniosp/machinepulse/issues/23).
- **Dependencies:** P02-003, P02-004.
- **Out of scope:** Derived feature, anomaly, and workflow event schemas.
- **Definition of done:** A versioned internal telemetry event has documented
  routing and fields, fixtures, and source traceability.

### P02-006 — Add consumer acknowledgement, retry, and dead-letter behavior

- **Status:** Planned
- **Outcome:** Internal consumers can retry transient failures and expose
  terminal failures without losing source identity.
- **Acceptance criteria:**
  - [ ] A failed processing attempt is not acknowledged as successful.
  - [ ] Retry count, backoff, and terminal failure behavior are configurable.
  - [ ] Dead-letter messages retain source identity and failure reason.
  - [ ] Duplicate delivery behavior is visible.
- **Tests or evidence:** Failure-injection/integration evidence for retry,
  acknowledgement, dead-letter, and duplicate handling.
- **GitHub issue:** [#24](https://github.com/gleniosp/machinepulse/issues/24).
- **Dependencies:** P02-005.
- **Out of scope:** Unbounded retry, exactly-once claims, and silent message
  dropping.
- **Definition of done:** Configured retry and terminal failure behavior is
  demonstrated, and dead-letter records are actionable and traceable.

### P02-007 — Prove the simulator-to-stream integration path

- **Status:** Planned
- **Outcome:** A repeatable local command demonstrates simulator telemetry
  traversing MQTT, the gateway, and the internal stream.
- **Acceptance criteria:**
  - [ ] A simulator run produces events observable in the internal stream.
  - [ ] Valid and invalid fixtures exercise the gateway path.
  - [ ] A repeatable integration command and result are documented.
- **Tests or evidence:** Documented command, captured stream output, valid and
  invalid fixture results, and CI/local result as available.
- **GitHub issue:** [#25](https://github.com/gleniosp/machinepulse/issues/25).
- **Dependencies:** P01-008, P02-006.
- **Out of scope:** Physical edge sensors and production deployment.
- **Definition of done:** The local core path can be replayed from a clean
  setup and its valid/invalid outcomes are recorded.

### P02-008 — Add initial ingestion observability

- **Status:** Planned
- **Outcome:** Operators can correlate gateway events and identify initial
  ingestion outcomes.
- **Acceptance criteria:**
  - [ ] Logs include correlation fields for device and event identity.
  - [ ] Metrics cover received, accepted, rejected, retried, and dead-lettered
    messages.
  - [ ] The Week 02 journal records baseline behavior.
- **Tests or evidence:** Structured log examples, metric names/output, and
  Week 02 journal entry.
- **GitHub issue:** [#26](https://github.com/gleniosp/machinepulse/issues/26).
- **Dependencies:** P02-003, P02-004.
- **Out of scope:** A full observability platform, distributed tracing, and
  production alerting policy.
- **Definition of done:** Core outcomes can be correlated by device/event and
  counted, and limitations are recorded in the journal.

## Phase definition of done

- [ ] All Phase 02 acceptance criteria are satisfied with evidence.
- [ ] The simulator-to-stream path works from documented local setup.
- [ ] Invalid and transient failure paths are observable and preserve source
  identity.
- [ ] The Week 02 journal records commands, results, and limitations.
- [ ] Local task and issue evidence are current; related issues remain open
  until their pull request is merged.
