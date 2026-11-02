# Internal telemetry events

- **Status:** Proposed for maintainer review
- **Version:** 0.1
- **Related issue:** [P02-005 / #23](https://github.com/gleniosp/machinepulse/issues/23)
- **Related contracts:** [Ingestion](ingestion.md), [Telemetry](telemetry-contract.md)

## Routing and envelope

The gateway publishes UTF-8 JSON records to Kafka topic
`machinepulse.telemetry.v1`. The Kafka key is the source `device_id` as UTF-8,
so a device's publications share a partition. Arrival order is not event-time
order. The local topic has one partition, replication factor one, delete
cleanup, and seven-day retention. Provision it explicitly; automatic topic
creation remains disabled. Production retention and replication need separate
capacity and availability decisions.

The envelope has four required fields:

| Field                 | Meaning                                                                                                              |
| --------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `schema_version`      | `internal.telemetry.v1`, independently versions this envelope                                                        |
| `source`              | Source `event_id`, `device_id`, `asset_id`, `occurred_at`, and `schema_version` strings copied without normalization |
| `gateway_received_at` | UTC RFC3339 timestamp for this gateway delivery attempt                                                              |
| `payload`             | Complete validated `telemetry.v1` JSON object                                                                        |

Payload values and timestamp strings retain their meaning and precision;
JSON whitespace may change during envelope serialization. `source` is an
index of the payload identity fields, not a second identity. Consumers must
reject unsupported envelope versions and inconsistent source/payload fields.
Additive fields may be ignored; incompatible changes require a new envelope
version and topic. The checked-in fixture under
`services/telemetry-gateway/internal/gateway/testdata/` is shared producer and
consumer compatibility evidence.

## Publication and delivery

The synchronous Kafka producer requires acknowledgement from all in-sync
replicas before returning success. Only then may the gateway acknowledge MQTT.
A timeout or failure leaves MQTT unacknowledged. The initial runtime requires
restart/reconnection to redeliver a pending failed attempt. A crash or ambiguous
publish result can duplicate a record. Consumers use source `event_id` for
idempotency; neither Kafka offsets nor receipt timestamps replace that ID.
Consumer acknowledgement, retry, and dead letters belong to P02-006.

Single-node acknowledgements establish broker acceptance, with durability
limited by the broker's persistent volume and filesystem. They do not establish
replica availability or power-loss durability. The gateway does not create
application topics or silently change broker policies.
