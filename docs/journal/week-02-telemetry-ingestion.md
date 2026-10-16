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
- [x] Local MQTT broker and event-stream environment starts with documented
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

## Day 2 — Local broker environment

### Plan

Implement P02-002 with explicit local MQTT and Kafka services, documented
readiness, and broker session persistence evidence before adding the gateway.

### What happened

Added the [Compose environment](../../infra/compose.yaml), Mosquitto persistence
configuration, named mise tasks, and the
[local infrastructure guide](../../infra/README.md). Image references pin
versions and multi-platform digests. The configuration requires no secrets and
publishes client ports on host loopback. The durable broker selection is
recorded in [accepted ADR-0005](../adr/0005-local-telemetry-brokers.md) after
maintainer approval on 2026-10-16.

The [smoke test](../../infra/smoke-test.sh) creates fresh disposable volumes,
waits for readiness, queues a non-retained QoS 1 message for an offline MQTT 5
session with a 24-hour expiry, and writes a Kafka record. It gracefully removes
and recreates containers, then verifies recovery of both messages. It cleans
up its isolated project and volumes. Root `test` and the PR workflow now invoke
this test; root `check` and the infrastructure hook validate Compose syntax.

### Evidence

Local validation on 2026-10-16, Linux amd64, Docker Engine 29.7.2 and Compose
5.4.0:

| Command or check | Result |
|---|---|
| `mise run infra:check` | Passed |
| `mise run infra:test` | Fresh startup and both persistence assertions passed; disposable services and volumes removed |
| `mise run infra:up` then `mise run infra:status` | Both services healthy; MQTT published on `127.0.0.1:1883`, Kafka on `127.0.0.1:9092` |
| Bundled MQTT client using the host listener | MQTT 5 CONNACK and QoS 1 PUBACK received |
| Bundled Kafka topic client using the host bootstrap listener | Topic listing returned successfully |
| `mise run check` | Passed: simulator lint, formatting, typing, 124 tests, Pixi lock check, and Compose validation |
| `mise run hooks:check` | Passed |

The host-listener probes used the pinned images' clients in temporary
containers with Linux host networking: `mosquitto_pub -h 127.0.0.1 -p 1883 -V
mqttv5 -q 1 -t machinepulse/health -m host-ready -d` and
`/opt/kafka/bin/kafka-topics.sh --bootstrap-server 127.0.0.1:9092 --list`.
The MQTT PUBACK reason was 16 (no matching subscribers), a successful broker
receipt for the health probe. The regular environment was stopped with
`mise run infra:down` after verification, preserving its volumes.

### What was learned and limits

MQTT 5 offline session/queue state and Kafka records survived graceful
container recreation with these pinned images. This does not prove recovery
from abrupt process failure or power loss. The environment has one instance of
each broker; arm64 image availability is pinned, but runtime evidence here is
amd64 only. CI execution awaits the maintainer's pull request.

P02-002 is locally complete. The smallest next step is P02-003: select the Go
MQTT client, verify deferred acknowledgement support, and implement the
gateway connection and subscription path.

## Weekly review

P02-001 and P02-002 are complete. The remaining Phase 02 outcomes require
gateway implementation and simulator-to-stream integration evidence.
