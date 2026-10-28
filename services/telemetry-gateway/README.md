# Telemetry gateway

The Go gateway receives device-facing MQTT telemetry using the accepted
[ingestion contract](../../docs/specs/ingestion.md). It validates `telemetry.v1`,
preserves exact payload bytes and producer metadata, and adds a separate UTC
receipt time. Invalid deliveries are durably quarantined before acknowledgement.
Valid deliveries reach an in-process handler; the internal event schema and
stream publication belong to P02-005.

## Run locally

For a container build and Compose workflow without host Go or mise, see the
[Docker quickstart](../../docs/guides/docker-quickstart.md).

From the repository root:

```bash
cp .env.example .env
mise run setup
mise run infra:up
mise run gateway:run
```

In another terminal, publish the existing contract fixture:

```bash
docker compose --file infra/docker/compose.yaml exec -T mqtt mosquitto_pub \
  -V mqttv5 -q 1 \
  -t machinepulse/v1/telemetry/01M000000028T5CY4GNF6YY4HM \
  -s < tools/simulator/tests/fixtures/telemetry.v1.json
```

JSON logs on stderr show `mqtt_subscribed`, `mqtt_connected`,
`telemetry_received`, and `telemetry_unacknowledged`. The command's valid-event
handler returns `ErrNoDisposition` until P02-005 supplies the stream sink, so a
valid delivery remains unacknowledged. The
one-message receive maximum pauses further QoS 1 deliveries, and restarting
with the same client ID redelivers the pending message while the broker
session survives. A producer PUBACK only confirms broker receipt.

To exercise rejection, publish an invalid fixture **before** the valid fixture
on a fresh gateway session; a pending valid delivery pauses later messages:

```bash
docker compose --file infra/docker/compose.yaml exec -T mqtt mosquitto_pub \
  -V mqttv5 -q 1 \
  -t machinepulse/v1/telemetry/01M000000028T5CY4GNF6YY4HM \
  -s < tools/simulator/tests/fixtures/telemetry-invalid/negative-rpm.json
```

Expect `telemetry_rejected` with a field path and reason code, then
`telemetry_quarantined` and `telemetry_disposition_complete`. The validation
counter log follows every attempt. A quarantine failure logs
`telemetry_quarantine_failed` and keeps the delivery pending for redelivery
after reconnection/restart. The initial runtime does not retry a failed
disposition on the same connection.

Stop with Ctrl-C. Use `mise run infra:down` to stop infrastructure while
preserving its data volumes. See the [infrastructure guide](../../infra/README.md)
for broker lifecycle and prerequisites.

## Configuration

The gateway process reads environment variables and command-line flags. Mise
loads local defaults from the repository-root `.env`, including when invoked
from this service directory. Copy `.env.example` on first setup and edit the
local copy; `.env` is gitignored. Existing files are never replaced by setup.

The precedence is an explicit flag, then an existing environment variable,
then the corresponding root `.env` value. `MACHINEPULSE_MQTT_ADDRESS` (or
`--broker`) is required: there is no implicit localhost address in the Go
configuration. Empty or missing optional variables use the Go tuning defaults;
invalid supplied values cause a startup error.

| Environment variable                       | Flag                  |
| ------------------------------------------ | --------------------- |
| `MACHINEPULSE_MQTT_ADDRESS`                | `--broker`            |
| `MACHINEPULSE_MQTT_CLIENT_ID`              | `--client-id`         |
| `MACHINEPULSE_MQTT_SESSION_EXPIRY_SECONDS` | `--session-expiry`    |
| `MACHINEPULSE_MQTT_RECONNECT_CAP`          | `--reconnect-cap`     |
| `MACHINEPULSE_MQTT_MAX_PACKET_BYTES`       | `--max-packet-bytes`  |
| `MACHINEPULSE_GATEWAY_OPERATION_TIMEOUT`   | `--operation-timeout` |
| `MACHINEPULSE_GATEWAY_QUARANTINE_DIR`      | `--quarantine-dir`    |
| `MACHINEPULSE_GATEWAY_TEMPERATURE_MIN`     | `--temperature-min`   |
| `MACHINEPULSE_GATEWAY_TEMPERATURE_MAX`     | `--temperature-max`   |
| `MACHINEPULSE_GATEWAY_ACCELERATION_MAX`    | `--acceleration-max`  |

`mise run gateway:run --help` lists defaults. `--broker` accepts a plain TCP
`host:port` for the local environment; `--client-id` must remain stable and
unique per running deployment. Session expiry, reconnect cap, operation
deadline, and inbound MQTT packet limit are configurable. The default packet
limit is 1 MiB; raise it explicitly for larger telemetry windows. The gateway
checks each MQTT frame's full size before the client allocates its body. An
oversized frame terminates the connection before application delivery, so it
cannot be quarantined.

The host quarantine default is `gateway-quarantine` relative to the process
working directory (`services/telemetry-gateway` for mise tasks). An absolute
path is recommended for deployments. The directory is created with mode 0700;
record files use 0600. It must support file and directory sync and hard links.
Compose mounts the `gateway-quarantine` named volume at
`/var/lib/machinepulse/quarantine`, owned by the runtime's non-root user. Retain
this volume across container recreation. Provision disk capacity; no automatic
cleanup or replay is implemented. The
[ingress quarantine contract](../../docs/specs/ingestion.md#local-ingress-validation-and-quarantine)
owns record fields, publication ordering, and durability limits.

Measurement bounds are optional, inclusive, finite deployment values: Celsius
for temperature and absolute m/s² for acceleration. Empty/unset values disable
each bound; minimum must not exceed maximum and acceleration maximum must be
non-negative. An explicit empty flag disables an environment-supplied bound.
No physical thresholds are assumed by default. Contract validation always
checks finite measurements and non-negative RPM. Source values and timestamps
are never clamped or rewritten.

`telemetry_validation_counters` logs process-local `received_total`,
`valid_total`, `invalid_total`, `quarantined_total`, and
`quarantine_failed_total`. Redeliveries count as new attempts; counters reset
on restart. `valid_total` means validation passed, not stream acceptance.

For staging or production, supply these variables in the process environment
and launch the built executable directly. The executable does not read `.env`
files or require mise. The address must be reachable from that process: a host
client uses the published host port, while a client on the Compose network can
use `mqtt:1883`. Deployment authentication/TLS remains separate follow-up work
under the [infrastructure guide](../../infra/README.md).

`MACHINEPULSE_MQTT_PORT` configures the local broker's published port; it does
not identify a remote broker. When changing that local port, update
`MACHINEPULSE_MQTT_ADDRESS` in `.env` or the environment to match.

## Development and evidence

```bash
mise run gateway:check
mise run gateway:test:integration
```

The integration test requires Docker and Compose. It creates an isolated
Mosquitto project with random host ports and fresh volumes, exercises the
actual gateway with the simulator's telemetry fixture, and removes its own
services and volumes. It covers deferred PUBACK, bounded in-flight delivery,
gateway restart redelivery, broker restart, and persistent subscription
recovery. It also records invalid deliveries in real file quarantine and proves
that a quarantine outage blocks the next message until restart/redelivery and
successful persistence. Valid-event test handlers simulate stream success.

Tests do not use `.env.test`: configuration unit tests inject environment
lookups, and the broker test discovers its isolated published address with
`docker compose port` before passing explicit configuration to the gateway.
Developer `.env` values do not select the test broker.

Project tasks also work from this directory; native `go test ./...`,
`go vet ./...`, and `go build ./...` remain available. The repository's
`go.work` coordinates this module. CI runs unit checks through the gateway
hook and runs the broker integration task explicitly.

## MQTT client

[Eclipse Paho Go v0.23.0](https://github.com/eclipse-paho/paho.golang/tree/v0.23.0)
provides MQTT 5 and manual acknowledgements through
`EnableManualAcknowledgment` and `Client.Ack`. The dependency is pinned in
`go.mod` and verified through `go.sum`. Its upstream source is dual licensed
under EPL-2.0 or BSD-3-Clause; this project uses it under BSD-3-Clause.

Each connection owns its Paho client and local session state. The gateway
reconnects with exponential backoff and jitter, inspects Session Present,
and reuses an existing subscription when the broker session survives. It
retries incomplete subscription setup after a rejected or missing SUBACK. Source QoS 1
delivery state remains at the broker across gateway process restarts.
This receive path does not implement a producer's outgoing publication buffer.

The handler interface returns success only after durable disposition; only
then does the gateway call `Ack`. Handlers must honor their context deadline.
Failures remain pending at the broker and are visible in structured logs.
The command connects validation and file quarantine; P02-005 connects stream
publication to the valid-event handoff. Context deadlines are checked between
filesystem operations; a blocked kernel filesystem call cannot be interrupted
by a Go context. [Week 02](../../docs/journal/week-02-telemetry-ingestion.md)
owns the recorded results and limits.
