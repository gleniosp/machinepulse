# Telemetry Contract

- **Status:** Draft
- **Contract version:** `telemetry.v1`
- **Scope:** Simulator and future physical edge producers

This is the first producer-facing contract for MachinePulse. It defines a telemetry window rather than an individual sample so vibration processing can operate on a meaningful bounded signal. It owns payload shape, field semantics, producer rules, validation, and compatibility; transport topology and downstream event contracts belong to later specifications.

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
  "event_id": "evt-00000001",
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
| `event_id` | Yes | Stable identifier for this telemetry window. It must remain unchanged across retries. |
| `device_id` | Yes | Identity of the producer that captured or generated the window. |
| `asset_id` | Yes | Asset associated with the window at production time. |
| `occurred_at` | Yes | Producer event time in UTC. This is not gateway receipt time. |
| `sequence` | Yes | Device-local sequence number used for ordering and gap detection. |
| `sampling.rate_hz` | Yes | Sampling rate for each vibration axis. |
| `sampling.sample_count` | Yes | Number of samples expected in each vibration axis. |
| `sampling.window_duration_ms` | Yes | Intended duration represented by the window. |
| `measurements.temperature_c` | Yes | Scalar temperature context in degrees Celsius. |
| `measurements.rpm` | Yes | Rotational speed context in revolutions per minute. |
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

## Simulator metadata

The simulator needs ground truth for experiments and evaluation. That metadata should be stored in a sidecar dataset or an experiment record keyed by `event_id`, for example:

```json
{
  "event_id": "evt-00000001",
  "simulator": {
    "seed": 1234,
    "condition": "imbalance",
    "severity": 0.7,
    "generator_version": "simulator.v1"
  }
}
```

This sidecar is not part of `telemetry.v1` and must not be available to production inference consumers as an input feature.

## Validation rules

The initial validator should check at least:

- required fields are present;
- identifiers are non-empty and conform to the selected identifier format;
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

1. Should identifiers use UUIDs, ULIDs, or readable development identifiers?
2. Is a one-second window and 1,600 Hz the right initial simulation default?
3. Should scalar temperature and RPM describe the start, end, or average of a window?
4. Should timestamps be producer-generated only, or should the gateway attach a separate receipt field to the internal event?
5. Which MQTT QoS provides the best initial balance between simplicity and delivery guarantees?
6. Should JSON remain the first internal event encoding or be converted at the gateway boundary?

These questions are intentionally visible. Their accepted answers should be recorded before the telemetry implementation is considered complete.

### Follow-up ownership

The questions are reviewed for the foundation phase and assigned to the
capability work that needs each decision:

| Question | Follow-up owner |
|---|---|
| Identifier format | P01-001 simulator specification and P02-001 ingestion specification |
| Initial window duration and sampling default | P01-001 simulator specification |
| Scalar temperature and RPM window semantics | P01-001 simulator specification, confirmed by P04-001 signal-processing specification |
| Producer event time and gateway receipt time | P02-001 ingestion specification |
| MQTT QoS and session behavior | P02-001 ingestion specification and its transport ADR |
| JSON as the initial internal encoding | P02-001 ingestion specification and its transport ADR |

These assignments keep the contract review complete without silently resolving
decisions that belong to the simulator or ingestion phases.
