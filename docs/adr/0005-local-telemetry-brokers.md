# ADR-0005 — Local telemetry brokers

- **Status:** Accepted
- **Date:** 2026-10-16
- **Decision owners:** Project maintainer
- **Related requirements:** FR-006–FR-010, NFR-003–NFR-006, NFR-011
- **Related specifications:** [Ingestion](../specs/ingestion.md), [Architecture overview](../architecture/overview.md)
- **Related experiments:** None
- **Supersedes:** None
- **Superseded by:** None

## Context

[P02-002](https://github.com/gleniosp/machinepulse/issues/20)
needs explicit local implementations of the accepted MQTT boundary and the
planned Kafka-compatible internal stream. The repository's initial deployment
direction is Docker Compose. No managed service or credentials should be
needed. MQTT session state must persist across broker restart under
[ADR-0004](0004-mqtt-delivery-semantics.md).

## Decision

Use Eclipse Mosquitto for MQTT and Apache Kafka in combined KRaft
broker/controller mode for the internal stream. The reviewable implementation
and exact image versions/digests live in [infra/docker/compose.yaml](../../infra/docker/compose.yaml).
The project maintainer accepted this decision on 2026-10-16.

Run one container per broker with named data volumes. Publish client ports on
host loopback and expose separate internal and host Kafka listeners. Configure
Mosquitto persistence, bounded offline queues, and graceful shutdown. Use
single-node Kafka replication settings and disable automatic topic creation;
application topic definitions remain with P02-005.

Keep the development environment credential-free, with anonymous MQTT and
plaintext Kafka restricted to the local host and Compose network. The
[infrastructure guide](../../infra/README.md) owns setup, configuration,
readiness, recovery, and verification commands. This is a local implementation
choice within the existing architecture; it does not settle production
broker deployment or security.

## Alternatives considered

### Another MQTT broker

A broker such as EMQX could satisfy MQTT 5 and persistent sessions. Mosquitto
provides the required broker behavior and bundled CLI clients in a small
official image, without needing a management UI or clustering for this slice.

### Another Kafka-compatible implementation

A compatible broker could reduce local resource use. Apache Kafka directly
implements the target protocol and provides its own administration and client
tools, avoiding an additional compatibility assumption for the first gateway.
Revisit if measured local resource use becomes a constraint.

### Multiple Kafka nodes or an external service

A replicated cluster can demonstrate availability, but adds runtime units and
failure cases before the first transport path works. A managed service would
add credentials and an external dependency. Use one local broker first and
record the resulting failure limitations explicitly.

## Consequences

### Positive

- Both boundaries have explicit upstream images pinned by digest.
- Contributors can exercise persistence and readiness with bundled clients.
- The stream uses Kafka's own protocol and tooling.

### Negative or accepted trade-offs

- Docker and Compose are host prerequisites outside mise's tool installation.
- A single Kafka JVM uses more resources than a lightweight protocol substitute.
- A single node has no replica availability; graceful restart evidence does
  not establish crash or power-loss durability.
- Local anonymous/plaintext listeners need a separate design before deployment
  beyond the trusted local environment.

### Follow-up work

- P02-003 selects a Go client and verifies MQTT deferred acknowledgement.
- P02-005 defines versioned internal event topics and envelopes.
- P02-007 demonstrates the actual simulator-to-stream path.

## Validation

Use `mise run infra:check` to validate Compose configuration and
`mise run infra:test` to demonstrate fresh startup, readiness, MQTT 5 offline
QoS 1 session recovery, and Kafka record recovery after container recreation.
Record actual commands, results, and limits in the
[Week 02 journal](../journal/week-02-telemetry-ingestion.md).

## References

- [Official Mosquitto image](https://hub.docker.com/_/eclipse-mosquitto)
- [Mosquitto configuration reference](https://mosquitto.org/man/mosquitto-conf-5.html)
- [Apache Kafka Docker guide](https://kafka.apache.org/41/getting-started/docker/)
- [Kafka broker configuration reference](https://kafka.apache.org/41/configuration/broker-configs/)
