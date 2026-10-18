# Week 02 — Telemetry Transport and Ingestion

- **Status:** In progress
- **Phase:** 02
- **Theme:** Move validated telemetry from MQTT into the internal event stream

## Goal

Implement the local MQTT-to-gateway-to-stream path while preserving
`telemetry.v1` identity, validating ingress, and making retries and failures
visible.

## Related documents

- [Phase 02 tasks](https://github.com/gleniosp/machinepulse/milestone/3)
- [Telemetry contract](../specs/telemetry-contract.md)
- [Ingestion and internal event boundaries](../specs/ingestion.md)
- [Accepted MQTT delivery ADR](../adr/0004-mqtt-delivery-semantics.md)

## Implementation scope

The [Phase 02 milestone](https://github.com/gleniosp/machinepulse/milestone/3)
and its issues own acceptance criteria and delivery progress. The entries below
record demonstrated behavior, commands, and limitations.

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
- [Phase 02 task plan](https://github.com/gleniosp/machinepulse/milestone/3)

## Day 2 — Local broker environment

### Plan

Implement P02-002 with explicit local MQTT and Kafka services, documented
readiness, and broker session persistence evidence before adding the gateway.

### What happened

Added the [Compose environment](../../infra/docker/compose.yaml), Mosquitto persistence
configuration, named mise tasks, and the
[local infrastructure guide](../../infra/README.md). Image references pin
versions and multi-platform digests. The configuration requires no secrets and
publishes client ports on host loopback. The durable broker selection is
recorded in [accepted ADR-0005](../adr/0005-local-telemetry-brokers.md) after
maintainer approval on 2026-10-16.

The [smoke test](../../infra/docker/broker-smoke-test.sh) creates fresh disposable volumes,
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

## Day 3 — Go MQTT gateway

### What happened

Implemented P02-003 in `services/telemetry-gateway`, with a native Go module,
root Go workspace, pinned mise Go toolchain, and project/root development
tasks. Added gateway checks to the repository hook and a disposable-broker
integration task to the pull-request workflow. The
[gateway guide](../../services/telemetry-gateway/README.md) owns commands,
configuration, client dependency provenance, and the current runtime limits.

The receive path preserves the exact producer JSON bytes, indexes source
identity without normalizing event time, and adds a separate UTC receipt time.
It exposes connection, subscription, received-message, and failure outcomes in
structured logs. Eclipse Paho's manual acknowledgement support was verified
against the pinned Mosquitto broker. The test withholds disposition, confirms
that the next delivery is backpressured, restarts the gateway with the same
client ID, and receives the original payload again. Simulated sink success
releases the next delivery; a subsequent broker restart recovers the existing
subscription and permits another publication.

### Evidence

Local validation on 2026-10-16, Linux amd64, Go 1.27.1 and Docker Engine 29.7.2:

| Command or check | Result |
|---|---|
| `mise run gateway:check` | Formatting, vet, compilation, dependency checksum verification, and unit tests with the race detector passed |
| `mise run gateway:test:integration` | MQTT 5 QoS 1 subscription, source preservation, deferred acknowledgement, bounded in-flight delivery, gateway redelivery, and broker/session recovery passed; disposable services and volumes removed |
| `mise run check` | Gateway checks, 124 simulator tests, simulator formatting/lint/typing, Pixi lock verification, and Compose validation passed |
| `prek run --files` with every tracked and new repository file | All applicable hooks passed, including gateway, simulator, infrastructure, and Pixi lock checks |
| `git diff --check` | Passed |

- [Gateway unit tests](../../services/telemetry-gateway/internal/gateway/gateway_test.go)
- [Broker integration test](../../services/telemetry-gateway/internal/gateway/broker_integration_test.go)
- [Gateway source](../../services/telemetry-gateway/internal/gateway/gateway.go)
- [P02-003 issue](https://github.com/gleniosp/machinepulse/issues/21)

### What was learned and limits

Docker can reassign a random host port when a container restarts. The first
broker-recovery test therefore retried an obsolete endpoint; the final harness
selects a free port and keeps its binding fixed for the disposable project.
A separate unit test caught and corrected acceptance of a URL-shaped broker
address where a numeric host port is required.

Final review also identified incomplete subscription setup after a rejected
SUBACK: the broker can preserve a session that has no accepted subscription.
The gateway now retries that setup on reconnect; a scripted MQTT protocol test
verifies the failure and recovery.

The command runs in observation mode and leaves messages unacknowledged,
applying a one-message receive limit until a durable handler is implemented.
Integration handlers simulate sink success; they do not establish quarantine
or Kafka durability. JSON decoding is not full `telemetry.v1` validation.
Actual ingress validation/quarantine, internal publication, and end-to-end
flow remain P02-004 onward. Recovery evidence covers graceful restarts, not
power loss, production authentication/TLS, or sustained-load behavior. The CI
compatibility follow-up below records the first pull-request run.

P02-003 is locally complete. The next task is P02-004: ingress validation and
durable invalid-message handling.

## Gateway configuration follow-up — 2026-10-17

Replaced the implicit localhost broker default with required external
configuration. The gateway command reads environment variables and accepts
explicit flag overrides; its library receives validated configuration and
never reads dotenv files or ambient environment state. The maintainer chose
root `.env` defaults for local mise commands and platform-provided variables
for deployed processes. The
[gateway configuration guide](../../services/telemetry-gateway/README.md#configuration)
owns the supported settings and precedence.

Added a versioned root `.env.example` and ignored root `.env` variants. Created
the local `.env` from the example only when it did not already exist. Root
mise uses its native dotenv parser to read local defaults into template
variables, then exports supported settings while preserving the caller's
existing environment. Direct file-to-environment loading would override the
caller, so it does not meet the accepted precedence. Defaults are anchored to
the root config and work from nested project commands.

Configuration tests use injected environment lookups. The broker integration
test continues to discover its disposable address and now passes that explicit
configuration through the gateway constructor before connecting. No static
`.env.test` or developer broker endpoint is used by the test.

Evidence:

- [Command configuration and tests](../../services/telemetry-gateway/cmd/telemetry-gateway/config_test.go)
- `mise run gateway:check` — Go formatting, vet, build, dependency verification,
  and unit tests with the race detector passed, including environment values,
  flag precedence over invalid environment values, missing/empty addresses,
  invalid numeric/duration settings, and help without configured services.
- Targeted mise environment probes from the root and service directories
  confirmed local `.env` defaults, exported-variable precedence, and explicit
  empty-variable precedence.
- `mise run gateway:test:integration` — passed; the dynamically selected broker
  was isolated from the developer's local `.env` and its resources were removed.
- `git check-ignore .env` — confirmed local configuration stays untracked.
- Repository hooks across tracked and new files passed, including gateway,
  simulator, infrastructure, and Pixi checks; `git diff --check` passed.

Local configuration still needs to align the MQTT client address with the
published port when that port changes. Container/deployment addresses depend
on the caller's network; authentication/TLS and actual deployed-runtime
verification remain future work.

## CI compatibility follow-up — 2026-10-17

The [first PR #100 CI run](https://github.com/gleniosp/machinepulse/actions/runs/39022587425)
failed during the integration test's broker restart: the runner's Compose
version rejects `start --wait`. Initial startup with `up --wait` and the earlier
delivery checks had succeeded. Changed restart to
`up --detach --no-recreate --wait --wait-timeout 60 mqtt`, retaining the same
container and data while using the supported readiness command.

`mise run gateway:test:integration` passed locally with the race detector after
the correction, including broker restart and persistent-session recovery;
`git diff --check` passed. A new CI run requires the maintainer to commit and
push this correction.

## Weekly review

P02-001 through P02-003 are complete. The remaining Phase 02 outcomes require
validation, durable disposition, internal publication, and simulator-to-stream
integration evidence.
