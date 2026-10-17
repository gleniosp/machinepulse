# Local telemetry infrastructure

This environment implements [P02-002](../docs/tasks/phase-02-telemetry-transport.md#p02-002--add-the-local-mqtt-and-event-stream-environment).
The broker selection and trade-offs are proposed in
[ADR-0005](../docs/adr/0005-local-telemetry-brokers.md).

## Prerequisites and start

Install Docker Engine or Docker Desktop with Docker Compose v2.20 or newer,
and start its daemon. Docker is a host prerequisite; `mise run setup` does not
install it. Allow roughly 2 GiB of free memory and disk space for the images
and local broker data. The image references in [compose.yaml](compose.yaml)
pin versions and multi-platform digests for Linux amd64 and arm64.

From the repository root:

```sh
mise run infra:check
mise run infra:up
mise run infra:status
```

No environment file or credentials are required. The first startup downloads
the images. `infra:up` waits up to 180 seconds for both services to become
healthy and exits unsuccessfully if they do not. MQTT readiness publishes a
non-retained MQTT 5 QoS 1 probe to `machinepulse/health`; Kafka readiness lists
topics through its internal listener. These checks prove broker availability;
the gateway and simulator-to-stream path are later Phase 02 work.

## Connections and configuration

| Service | Host client address | Client in the Compose network |
|---|---|---|
| MQTT | `127.0.0.1:1883` | `mqtt:1883` |
| Kafka bootstrap | `127.0.0.1:9092` | `kafka:19092` |

Kafka uses separate advertised listeners for host and container clients. Its
controller listener stays inside the Compose network. Application stream
topics are not created here; P02-005 owns their names and envelopes.

If a default port is occupied, export the overrides before starting services
and keep them set for later commands:

```sh
export MACHINEPULSE_MQTT_PORT=21883
export MACHINEPULSE_MQTT_ADDRESS=127.0.0.1:21883
export MACHINEPULSE_KAFKA_PORT=29092
mise run infra:up
```

The Kafka override changes both the published host port and advertised host
address. Container client addresses stay as listed above. Use positive port
numbers for a usable host Kafka listener.

The same overrides can be kept in a gitignored root `.env`, copied from
`.env.example`; mise loads it consistently for root and project commands.
Already exported environment values take precedence. The MQTT address is
client configuration, so keep it aligned with the published MQTT port when
running a gateway on the host. See the
[gateway configuration guide](../services/telemetry-gateway/README.md#configuration).

Both published ports bind to IPv4 loopback. MQTT permits anonymous clients;
Kafka uses plaintext without authentication. This is a trusted local development
environment. Containers attached to its network can also connect. Networked
or production deployment needs a separate security and operations design.

The [Mosquitto configuration](mosquitto/mosquitto.conf) owns broker persistence
and offline queue limits. MQTT clients request session expiry; the accepted
[ingestion contract](../docs/specs/ingestion.md#sessions-and-reconnects) owns
the protocol and client behavior. The Compose file owns Kafka settings and
image pins. Update a version and its digest together after running the smoke
test. No broker binaries or client libraries need to be installed on the host.

## Persistence and stopping

```sh
mise run infra:down
```

This removes the containers and network while preserving the `mqtt-data` and
`kafka-data` named volumes. A later `infra:up` reuses the data. MQTT snapshots
session state and queued messages periodically and on graceful shutdown.
Kafka retains its KRaft metadata and records in its data volume. Preserve the
Compose project name (`machinepulse`) to reuse the same volumes.

The environment has one instance of each broker and Kafka replication factor
one. Persistence across a graceful restart does not establish power-loss
durability or availability during broker failure. MQTT offline queues are
bounded; the producer replay/buffer path remains necessary.

To inspect a startup failure:

```sh
mise run infra:status
mise run infra:logs
```

Check that Docker is running, the host ports are free, and the host has enough
memory/disk space. An unhealthy Kafka container may need its logs inspected
for listener, data-directory, or cluster-identity errors. Do not change the
cluster ID for an existing Kafka volume. Avoid deleting volumes to resolve a
failure unless their data is intentionally disposable.

## Repeatable verification

```sh
mise run infra:test
```

The [smoke test](smoke-test.sh) starts an isolated Compose project with fresh
volumes and random loopback host ports. It registers an offline MQTT 5
subscription with a 24-hour expiry, publishes a non-retained QoS 1 message,
and writes a Kafka record with `acks=all`. It then gracefully removes and
recreates the containers, and asserts that both messages can be recovered.
It tests the internal listeners; the random host ports are not host Kafka
bootstrap addresses. The test removes only its own disposable project and
volumes, including on failure, and prints diagnostic logs on failure.

`mise run test` includes this test and requires a running Docker daemon.
`mise run check` and the infrastructure pre-commit hook validate the Compose
configuration without starting containers; they require the Docker CLI and
Compose plugin. The PR workflow also runs the smoke test.

## Upstream references

- [Apache Kafka Docker guide](https://kafka.apache.org/41/getting-started/docker/)
- [Kafka broker configuration](https://kafka.apache.org/41/configuration/broker-configs/)
- [Mosquitto broker configuration](https://mosquitto.org/man/mosquitto-conf-5.html)
- [Mosquitto subscription client](https://mosquitto.org/man/mosquitto_sub-1.html)
