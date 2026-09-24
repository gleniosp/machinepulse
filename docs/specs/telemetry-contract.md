# Telemetry Contract

- **Status:** Draft
- **Contract version:** `telemetry.v1`
- **Scope:** Simulator and future physical edge producers
- **Related ADR:** [ADR-0001 — Telemetry event identifiers](../adr/0001-telemetry-event-identifiers.md)

This is the first producer-facing contract for MachinePulse. The product
[domain model](../product/domain-model.md#telemetry-window) defines what a
telemetry window represents. A window groups the vibration samples from a
finite interval and associates scalar temperature/RPM context with that
interval in one identified event. The bounded vibration samples provide the
time history needed for signal features, while sampling metadata makes their
timing explicit. Temperature and RPM may come from sensors with different,
slower update rates; they do not need arrays matching the vibration sample
count. Grouping the data this way gives transport, validation, storage, and
replay a common unit. This contract owns payload shape, field semantics,
producer rules, validation, and compatibility; transport topology and
downstream event contracts belong to later specifications.

## Design goals

The contract must be:

- implementable by the Python simulator and a later edge producer;
- explicit about units and timing;
- easy to inspect during local development;
- versionable without silently breaking consumers;
- traceable through retries and reprocessing; and
- independent of the analytical model used downstream.

JSON is the initial wire representation because it is inspectable and simple for the first local system. A compact encoding may be evaluated later if benchmarks justify it.

## Event shape

The following is the proposed `telemetry.v1` shape. Field names and units are subject to review before implementation begins.

```json
{
  "schema_version": "telemetry.v1",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_id": "device-0001",
  "asset_id": "asset-0001",
  "occurred_at": "2026-09-02T12:20:31.112Z",
  "sequence": 42,
  "sampling": {
    "rate_hz": 1600,
    "sample_count": 1600,
    "window_duration_ms": 1000
  },
  "measurements": {
    "temperature_c": 42.7,
    "rpm": 1794.0,
    "vibration_m_s2": {
      "x": [0.12, -0.04, 0.08],
      "y": [0.07, -0.02, 0.05],
      "z": [0.21, 0.11, -0.03]
    }
  }
}
```

The shortened arrays in the example are illustrative only. A valid event must satisfy the declared `sample_count`.

## Field semantics

| Field | Required | Meaning |
|---|---:|---|
| `schema_version` | Yes | Version of the external telemetry contract. |
| `event_id` | Yes | Canonical lowercase, hyphenated UUID unique to this telemetry window across the deployment. A producer assigns it once and preserves it across retries. |
| `device_id` | Yes | Identity of the producer that captured or generated the window. |
| `asset_id` | Yes | Asset associated with the window at production time. |
| `occurred_at` | Yes | UTC time of the first vibration sample in the represented window. This is not gateway receipt time. |
| `sequence` | Yes | Device-local sequence number used for ordering and gap detection. |
| `sampling.rate_hz` | Yes | Sampling rate for each vibration axis. |
| `sampling.sample_count` | Yes | Number of samples expected in each vibration axis. |
| `sampling.window_duration_ms` | Yes | Intended duration represented by the window. |
| `measurements.temperature_c` | Yes | Temperature context in degrees Celsius, representative of the window midpoint. |
| `measurements.rpm` | Yes | Rotational speed context in revolutions per minute, representative of the window midpoint. |
| `measurements.vibration_m_s2.x` | Yes | X-axis acceleration samples in metres per second squared. |
| `measurements.vibration_m_s2.y` | Yes | Y-axis acceleration samples in metres per second squared. |
| `measurements.vibration_m_s2.z` | Yes | Z-axis acceleration samples in metres per second squared. |

## Producer-side rules

A producer should:

- generate or capture exactly the declared number of samples per axis;
- use the declared sampling rate when constructing the window;
- use UTC timestamps with an explicit timezone representation;
- preserve `event_id` when retrying publication;
- increment `sequence` for each new window for a device;
- avoid placing analytical predictions in the raw telemetry event; and
- record simulator configuration and ground-truth condition outside the production contract.

`occurred_at` is the timestamp of the first vibration sample. Each event
contains one scalar `temperature_c` and one scalar `rpm` value representing
context for the window midpoint; the underlying sensors need not physically
sample at the vibration rate or exactly at that midpoint. A producer should
associate its available lower-rate reading with the relevant window and
document its acquisition method. The signal-processing specification should
confirm that midpoint context is suitable before the contract is accepted.

## Simulator metadata

For simulator runs, the condition and intensity are reference labels describing
the synthetic scenario used to generate an event. Store them outside
`telemetry.v1`, in a sidecar dataset or experiment record keyed by `event_id`,
for example:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "simulator": {
    "seed": 1234,
    "condition": "imbalance",
    "condition_intensity": 0.7,
    "generator_version": "simulator.v1"
  }
}
```

The sidecar is not part of `telemetry.v1`. Experiments may join it to telemetry
to evaluate analysis results, but production inference must not receive these
labels as input features. The [simulator behavior specification](simulator.md#ground-truth-sidecar)
defines their meaning and limitations.

`event_id` is an opaque event identity; consumers use `sequence` for device-local
ordering and gap detection. Physical producers should use UUIDv7 where
available, with UUIDv4 as a supported alternative. The simulator uses
deterministic UUIDv5 values as specified by the
[simulator behavior specification](simulator.md#window-timing-and-identity).
The UUID generation profiles and their rationale are recorded in
[ADR-0001](../adr/0001-telemetry-event-identifiers.md).

## Validation rules

The initial validator should check at least:

- required fields are present;
- `event_id` is a valid UUID in canonical lowercase, hyphenated form, and
  other identifiers are non-empty and conform to their selected formats;
- `schema_version` is supported;
- `occurred_at` is parseable and has timezone information;
- `sampling.rate_hz` is positive;
- `sampling.sample_count` is positive;
- `window_duration_ms` is positive and consistent with the sampling configuration within the chosen tolerance;
- all three vibration axes contain the declared sample count;
- all numeric values are finite;
- RPM is not negative;
- temperature and acceleration values are within configurable ingestion bounds; and
- the event identity has not already been accepted as a duplicate.

Bounds should be configurable rather than presented as universal physical truths. A value outside a configured bound may be quarantined for investigation instead of being silently clamped.

## Ordering and duplicates

`sequence` is local to a device. Consumers should not assume that events arrive in sequence order.

The initial system assumes at-least-once delivery. A retry must reuse `event_id`, allowing consumers to detect duplicates. Duplicate handling must be documented separately for:

- raw event persistence;
- feature calculation;
- anomaly observations; and
- alert creation.

## Transport and downstream boundaries

MQTT is the initial device-facing transport, but broker topic naming, subscriptions, retained messages, and QoS are ingestion concerns rather than payload fields. They should be defined in the ingestion specification and an ADR before implementation.

Internal event envelopes and derived-event schemas are separate contracts. The [architecture data flow](../architecture/data-flow.md) describes their role; the relevant capability specifications will define their fields when those phases are prepared. They must preserve the source event identity and contract version.

## Evolution rules

- Additive optional fields may be introduced without changing the major contract version.
- Removing or changing the meaning of a required field requires a new contract version.
- Changing units requires a new field or contract version; consumers must not infer units.
- Consumers should reject unsupported major versions clearly.
- Fixtures for supported versions should remain in the repository.

## Open questions before implementation

1. Is a one-second window and 1,600 Hz the right initial simulation default?
2. Should the proposed midpoint semantics for scalar temperature and RPM be retained for all producers?
3. Should timestamps be producer-generated only, or should the gateway attach a separate receipt field to the internal event?
4. Which MQTT QoS provides the best initial balance between simplicity and delivery guarantees?
5. Should JSON remain the first internal event encoding or be converted at the gateway boundary?

These questions are intentionally visible. Their accepted answers should be recorded before the telemetry implementation is considered complete.

### Follow-up ownership

The questions are reviewed for the foundation phase and assigned to the
capability work that needs each decision:

| Question | Follow-up owner |
|---|---|
| Event ID generation and retry identity | P01-001 simulator specification and ADR-0001; P02-001 defines ingestion validation and idempotency handling |
| Initial window duration and sampling default | P01-001 simulator specification |
| Scalar temperature and RPM window semantics | P01-001 proposes midpoint semantics for the simulator; P04-001 confirms or revises the contract-wide convention |
| Producer event time and gateway receipt time | P02-001 ingestion specification |
| MQTT QoS and session behavior | P02-001 ingestion specification and its transport ADR |
| JSON as the initial internal encoding | P02-001 ingestion specification and its transport ADR |

These assignments keep the contract review complete without silently resolving
decisions that belong to the simulator or ingestion phases.
