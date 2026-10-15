# ADR-0004 — MQTT delivery semantics

- **Status:** Accepted
- **Date:** 2026-10-15
- **Updated:** 2026-10-15
- **Decision owners:** Project maintainer
- **Related requirements:** FR-006–FR-010, NFR-003–NFR-006, NFR-011
- **Related specifications:** [Ingestion and internal event boundaries](../specs/ingestion.md)
- **Related experiments:** None
- **Supersedes:** None
- **Superseded by:** None

## Context

MachinePulse needs a device-facing MQTT path that can reconnect, tolerate
duplicate delivery, distinguish broker receipt from platform acceptance, and
cross into a separately versioned internal event stream. MQTT session and
acknowledgement semantics affect broker configuration, edge producer behavior,
and the Go gateway client.

## Decision

Use MQTT 5.0 with QoS 1, non-retained telemetry windows, and persistent
gateway and producer sessions with a configurable 24-hour initial expiry. The
gateway acknowledges a QoS 1 delivery only after a valid event is accepted by
the internal stream or an invalid event is durably quarantined. Producer
`event_id` remains the application-level duplicate identity. The device topic
is `machinepulse/v1/telemetry/{device_id}`; internal event names and
schemas remain owned by P02-005.

The maintainer accepted this decision on 2026-10-15. P02-002 and P02-003 must
confirm that the selected broker and Go client support persistent sessions
and deferred acknowledgements before relying on those behaviors at runtime. If
the selected client cannot meet the acknowledgement ordering, revise this ADR
before implementation rather than weakening the durability boundary silently.

## Alternatives considered

### MQTT 3.1.1

It offers broad compatibility and could support QoS 1 plus persistent
sessions. Its Clean Session model is less explicit than MQTT 5.0 session expiry
and it lacks MQTT 5.0 acknowledgement reason codes. Retain it as the fallback
if implementation compatibility outweighs these capabilities.

### QoS 0

QoS 0 has no protocol acknowledgement or retransmission. It is simpler but
does not meet the initial ingestion path's need to observe and retry delivery
across ordinary network interruptions.

### QoS 2

QoS 2 adds a multi-step transport handshake but does not make downstream
database or stream side effects exactly once. The application still needs
idempotency keyed by `event_id`; use QoS 1 and exercise duplicate handling.

### Retained telemetry

A retained message would provide a last-value snapshot to a new subscriber, but
historical telemetry windows are not current-state snapshots. Use session
queues and producer buffering/replay for their distinct purposes.

## Consequences

### Positive

- Protocol receipt, gateway disposition, and internal stream acceptance have
  separate meanings.
- QoS 1 retries preserve at-least-once delivery while event identity makes
  duplicates traceable.
- The gateway can recover a subscription session after a temporary outage.
- Internal routing remains independent from public device topic layout.

### Negative or accepted trade-offs

- QoS 1 can redeliver, so consumers need idempotent behavior.
- The broker must persist gateway session state, and its storage limits bound
  outage recovery.
- MQTT 5.0 and deferred acknowledgement support must be verified in the chosen
  Go client and local broker.
- A 24-hour session expiry is an initial configuration value, not an
  end-to-end retention guarantee.

### Follow-up work

- P02-002 configures and demonstrates local broker session persistence.
- P02-003 verifies Go-client protocol and deferred-ack support.
- P02-004 implements validation and durable invalid-message handling.
- P02-005 defines internal event topic names and envelope fields.
- P02-006 defines consumer retry, acknowledgement, and dead-letter behavior.
- P08-004 owns durable physical edge buffering and sequence handling.

## Validation

Validate broker and gateway reconnect behavior,
QoS 1 duplicate delivery, terminal-disposition acknowledgement, and separation
between MQTT topics and internal stream topics in the Phase 02 integration path.
