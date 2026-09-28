# ADR-0001 — Telemetry event identifiers

- **Status:** Accepted
- **Date:** 2026-09-24
- **Updated:** 2026-09-28
- **Decision owners:** Project maintainer
- **Related requirements:** FR-001, NFR-001
- **Related specifications:** [Telemetry contract](../specs/telemetry-contract.md), [Simulator behavior](../specs/simulator.md)
- **Related experiments:** None
- **Supersedes:** None
- **Superseded by:** None

## Context

Every telemetry window needs a stable identity. Consumers use that identity to
detect retried deliveries and to join a simulator window to its separately
stored ground-truth record. Producers can be distributed edge devices that
may generate and buffer events while offline. The simulator also needs to
reproduce the same event IDs when it regenerates the same run.

The contract already carries a device-local `sequence` for ordering and gap
detection. Event identity therefore does not need to encode order.

## Decision

Use canonical lowercase, hyphenated UUID strings for `event_id` throughout
`telemetry.v1`. Producers assign the ID once per window and retain it with the
event across retries. UUIDs let independent producers create event IDs without
coordinating through a central counter.

- The simulator generates deterministic UUIDv5 values in the fixed MachinePulse
  telemetry namespace `137bfca0-3f75-56ce-a36c-932f0bc60c36`, derived from the
  stable tuple `(device_id, run_id, sequence)`. The namespace is UUIDv5 of the
  URL namespace and `https://github.com/gleniosp/machinepulse/telemetry`.
  P01-002 locks the namespace and compact JSON-array tuple encoding in a
  repeatability fixture; the simulator specification owns the exact encoding.
- Physical producers should use UUIDv7 where available. UUIDv4 is also
  supported where UUIDv7 generation is unavailable.
- Consumers use the device-local `sequence` for ordering and gap detection;
  event IDs are opaque identifiers and do not define event order.

The `event_id` is required to be unique for each distinct window across the
deployment. Distinct simulator runs use distinct `run_id` values. A retry
reuses the original ID rather than creating a new one.

## Alternatives considered

### One global incrementing counter

A counter is compact, readable, and naturally ordered. One counter shared by
all producers requires coordination and becomes unavailable to an offline
producer. A producer-local counter needs a producer or session scope to avoid
collisions, and it must be persisted across restarts. The existing sequence
field already provides device-local ordering, so the event ID does not need to
repeat that responsibility.

### UUIDv4 for every producer

UUIDv4 supports independent generation without a shared allocator and is a
valid fallback for physical producers. Random generation does not naturally
reproduce the simulator's IDs when the same run is generated again, so the
simulator would need to persist an ID mapping or use a deterministic method.

### UUIDv7 for every producer

UUIDv7 supports independent generation and approximate time ordering, which
can improve database index locality. Its timestamp reflects the producer's
clock and is not a reliable ordering source across devices; `sequence` remains
the ordering field. A newly generated UUIDv7 would also change on a simulator
rerun, so the simulator uses UUIDv5 instead.

### ULID or a readable composite identifier

ULID provides a time-sortable identifier, and a readable composite can expose
producer or sequence details. Either would add another identifier format to
implement and validate without a needed benefit over UUIDs for the current
contract.

## Consequences

### Positive

- Edge producers can create IDs independently, including while disconnected.
- Retries and simulator sidecars use a stable per-window identity.
- One UUID syntax works for both simulated and physical telemetry.
- Ordering remains explicit in the device-local sequence field.

### Negative or accepted trade-offs

- UUID strings are longer than counters and take more space in textual payloads.
- UUIDv7 reveals an approximate event creation time; its order is not a
  substitute for the device-local sequence or event timestamp.
- UUIDv5 depends on keeping its namespace and deterministic event-name
  encoding stable; P01-002 records these in a repeatability fixture.

### Follow-up work

- P01-002 must implement and fixture the simulator UUIDv5 namespace and name
  encoding.
- P02-001 must validate UUID syntax and define the persistence scope for
  idempotency records.

## Validation

P01-002 compares event IDs as part of repeatability evidence for identical
simulator runs. P01-006 validates the canonical UUID form. Ingestion evidence
will verify that a retry carrying the same event ID is treated as a duplicate
according to its idempotency policy.

## References

- [RFC 9562 — Universally Unique IDentifiers (UUIDs)](https://www.rfc-editor.org/rfc/rfc9562.html)
- [CloudEvents specification — `id` and `source`](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md)
