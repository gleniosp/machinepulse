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

## Consumer disposition (P02-006 proposal)

The initial Go consumer processes records serially in a consumer group using
explicit synchronous offset commits. A handler must return success only after
its side effect is durable and use source `event_id` for idempotency. No domain
storage handler is introduced by this transport slice.

Configuration supplies a maximum number of attempts (including the first), a
fixed positive backoff, an operation timeout, and terminal policy (`stop` or
`dead-letter`). Each attempt has its own deadline. Cancellation stops without
committing. Exhaustion under `stop` returns an error without committing. Under
`dead-letter`, publication to `machinepulse.telemetry.dead-letter.v1` must be
acknowledged by all in-sync replicas before committing the source offset. A
publication or commit failure stops intake; restarting the same group may
redeliver the record. Topics must be provisioned explicitly with the same local
retention/replication policy as the source topic.

Dead-letter JSON contains `schema_version` (`internal.dead-letter.v1`), the
original Kafka record bytes (base64), key, topic, partition, offset, consumer
group, attempt count, final failure reason, and UTC failure time. Original bytes
retain source identity even for an invalid envelope. Consumers reject unsupported
versions, missing identities, mismatched source/payload identity, and a device
key that differs from source identity before calling the handler.

Structured attempt and disposition logs include source event/device identity,
group, topic, partition, offset, attempt number and failure. Repeated event IDs
are intentionally passed to handlers: these correlation fields expose duplicates
without an unbounded in-memory deduplication cache. Ambiguous commits, crashes,
and rebalances can duplicate successful processing or dead letters. Attempt
budgets restart on redelivery; this is at-least-once delivery, with no automatic
replay or exactly-once guarantee. The caller owns reader/writer closure after Run
returns and must run only one loop per reader with auto commits disabled.
