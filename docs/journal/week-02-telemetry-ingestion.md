# Week 02 — Telemetry Transport and Ingestion

- **Status:** In progress
- **Phase:** 02
- **Theme:** Move validated telemetry from MQTT into the internal event stream

## Goal

Implement the local MQTT-to-gateway-to-stream path while preserving
`telemetry.v1` identity, validating ingress, and making retries and failures
visible.

## Related documents

- [Phase 02 tasks](../tasks/phase-02-telemetry-transport.md)
- [Telemetry contract](../specs/telemetry-contract.md)
- [Ingestion and internal event boundaries](../specs/ingestion.md)
- [Accepted MQTT delivery ADR](../adr/0004-mqtt-delivery-semantics.md)

## Planned outcomes

- [x] MQTT topics and delivery semantics are reviewed and accepted.
- [ ] Local MQTT broker and event-stream environment starts with documented
  readiness behavior.
- [ ] Go gateway validates and routes telemetry with source event time and
  identity preserved.
- [ ] Invalid messages, retries, and dead-letter outcomes have tested and
  observable behavior.
- [ ] A repeatable simulator-to-stream integration command and evidence are
  recorded.

## Day 1 — Ingestion contract review

### Plan

Prepare the P02-001 ingestion specification and task breakdown before runtime
implementation, because the topic layout, delivery acknowledgement, session,
and event-time boundaries are prerequisites for the gateway and broker setup.

### What happened

Prepared the MQTT device route, QoS 1 delivery, persistent gateway and producer
sessions, non-retained source windows, terminal-disposition acknowledgement,
and separate producer event time and gateway receipt time. Added ADR-0004 for
the durable transport choices and mapped all eight Phase 02 GitHub issues into
the local task plan. The maintainer approved P02-001 and accepted the
specification and ADR on 2026-10-15; all three task acceptance criteria are
complete.

No runtime implementation or automated checks were run for this documentation
preparation. The specification identifies the required broker/client
compatibility checks and end-to-end evidence for later Phase 02 tasks.

### Evidence

- [P02-001 issue](https://github.com/gleniosp/machinepulse/issues/19)
- [Accepted ingestion specification](../specs/ingestion.md)
- [Accepted ADR-0004](../adr/0004-mqtt-delivery-semantics.md)
- [Phase 02 task plan](../tasks/phase-02-telemetry-transport.md)

## Weekly review

P02-001 is complete. The remaining Phase 02 outcomes require runtime
implementation and integration evidence.
