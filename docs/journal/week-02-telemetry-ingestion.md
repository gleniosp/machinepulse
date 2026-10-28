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

| Command or check                                             | Result                                                                                         |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| `mise run infra:check`                                       | Passed                                                                                         |
| `mise run infra:test`                                        | Fresh startup and both persistence assertions passed; disposable services and volumes removed  |
| `mise run infra:up` then `mise run infra:status`             | Both services healthy; MQTT published on `127.0.0.1:1883`, Kafka on `127.0.0.1:9092`           |
| Bundled MQTT client using the host listener                  | MQTT 5 CONNACK and QoS 1 PUBACK received                                                       |
| Bundled Kafka topic client using the host bootstrap listener | Topic listing returned successfully                                                            |
| `mise run check`                                             | Passed: simulator lint, formatting, typing, 124 tests, Pixi lock check, and Compose validation |
| `mise run hooks:check`                                       | Passed                                                                                         |

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

| Command or check                                              | Result                                                                                                                                                                                                |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mise run gateway:check`                                      | Formatting, vet, compilation, dependency checksum verification, and unit tests with the race detector passed                                                                                          |
| `mise run gateway:test:integration`                           | MQTT 5 QoS 1 subscription, source preservation, deferred acknowledgement, bounded in-flight delivery, gateway redelivery, and broker/session recovery passed; disposable services and volumes removed |
| `mise run check`                                              | Gateway checks, 124 simulator tests, simulator formatting/lint/typing, Pixi lock verification, and Compose validation passed                                                                          |
| `prek run --files` with every tracked and new repository file | All applicable hooks passed, including gateway, simulator, infrastructure, and Pixi lock checks                                                                                                       |
| `git diff --check`                                            | Passed                                                                                                                                                                                                |

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

## Delivery tooling — 2026-10-27

Delivered the tooling scope of [#107](https://github.com/gleniosp/machinepulse/issues/107)
and reviewed follow-ups on commits `0218031` and `31dfb0a`.
The [tooling guide](../developer-tooling.md) owns commands, formatter/fixture
boundaries, and editor setup; the [working agreement](../working-agreement.md)
owns delivery permissions and review. The existing delivery skills and new
PR template link to those owners.

Evidence from the initial implementation and review:

- Locked Pixi 0.83.0, Commitizen 4.19.3 in the existing `dev` environment,
  and dprint 0.64.3 with the checksum-pinned Oxc plugin. Locked installs and
  the updated simulator Docker build passed; the runtime dependency set was
  unchanged.
- Checked 14 valid/invalid message cases through the direct task and a
  disposable installed hook, including a filename with spaces. The temporary
  verification script was subsequently removed during review.
- Unit/integration verification passed: 124 simulator tests, Go race-enabled
  unit tests, broker persistence, gateway recovery, and container builds/datasets.
  An initial exact-serialization failure identified the golden-fixture formatting
  boundary; fixtures were restored and excluded before the successful run.
- `mise run fix` and `mise run hooks:check` passed after separating tests from
  hooks. Reviewed Oxc's tagged schema and verified Markdown formatting via stdin.
  The two updated skills passed the skill-creator validator.

Final task/documentation review:

- Ordered root commands before shared and project tasks. Main `check` now
  explicitly calls formatting, lint, and type checking, then dependency/config
  checks. Project task definitions were unchanged apart from ordering.
- Audited all 69 task definitions and their `run`/`depends` edges: no missing
  targets or cycles, and no duplicate leaf execution within `check` (11 leaves),
  `fix` (15), or `test` (5). Each language typecheck appears once in `check`;
  no test tasks are reachable from `check` or `fix`.
- `mise run check` passed with mypy covering 23 Python files, Go vet/build/module
  verification, formatting/lint, Pixi lock validation, Compose validation, and
  shell syntax. No tests were rerun for this task-order/documentation-only review.
- Documented the exact-text goldens and the broader fixture exclusion, shortened
  repeated tooling/workflow prose, and consolidated this evidence.
  `git diff --check` passed.

The [first PR #108 CI run](https://github.com/gleniosp/machinepulse/actions/runs/40559746666)
failed before repository checks: mise 2026.8.11's bundled dprint recipe lacked
attestation metadata required by the lockfile generated with mise 2026.10.20.
Aligned the repository minimum and CI pin to 2026.10.20. Regenerating `mise.lock`
left its pins, checksums, and provenance unchanged. A fresh installation of all
five tools with isolated configuration/data/cache directories and
`MISE_LOCKED_VERIFY_PROVENANCE=true` passed, including dprint 0.64.3.
`mise run check` and `git diff --check` also passed for the correction.

The fresh-install verification ran on local Linux amd64. Interactive VS Code
behavior remains unverified; hosted CI results are tracked on PR #108.

## Ingress validation and quarantine — 2026-10-28

Implemented the local slice for
[P02-004 / #22](https://github.com/gleniosp/machinepulse/issues/22) on
`feat/22-ingress-validation`. The
[ingestion specification](../specs/ingestion.md#local-ingress-validation-and-quarantine)
contains the proposed local policy for maintainer review; the
[gateway guide](../../services/telemetry-gateway/README.md) owns configuration
and operator commands. No additional runtime dependency was introduced.

### What was demonstrated

The gateway accepts the shared producer fixture and rejects all nine shared
invalid fixtures with actionable reasons. Additional Go tests cover ambiguous
JSON, strict integer types, identifier profiles, UTC event time, exact sampling
arithmetic beyond machine integer range, missing/unknown fields, finite scalar
and axis values, sample counts, topic/device matching, delivery policy, and
optional inclusive deployment bounds. Repeated valid event IDs reach the valid
handler without changing source bytes or timestamp text.

File quarantine preserves arbitrary bytes (including invalid UTF-8) through
base64 encoding and a SHA-256 digest, along with receipt/transport metadata,
recoverable source fields, and the rejection reason. Unit tests verify records
remain readable after reopening, retries do not overwrite earlier records,
private file permissions, counter/log output, and acknowledgement gating on
storage errors, cancellation, and expired disposition. A failed acknowledgement
does not remove the quarantine record.

The real Mosquitto test demonstrated that an invalid delivery reaches file
quarantine before the next valid event can pass the one-message receive limit.
An injected quarantine outage prevented that next delivery. After a gateway
restart, the invalid bytes were redelivered intact, persisted, and acknowledged,
releasing the queued valid event. Existing gateway/broker restart and session
recovery assertions also passed.

The application container test wrote quarantine as UID 65532 into its named
volume and verified exact malformed bytes, digest, reason, and transport fields
after initial receipt, gateway restart, and full container recreation. The valid
fixture remained pending and retained its source identity through those stages.
The disposable containers, images, networks, and volumes were removed by the
test harness.

### Validation evidence

Local Linux amd64, pinned Go 1.27.1 and repository toolchain:

| Command                             | Result                                                                                                                                        |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `mise run gateway:test`             | Go unit tests passed with the race detector                                                                                                   |
| `mise run gateway:test:integration` | Real-broker acknowledgement, quarantine outage/redelivery, and recovery assertions passed                                                     |
| `mise run fix`                      | Formatting and all repository checks passed, including Go vet/build/module checks, Python lint/types, lockfile, Compose, and shell syntax     |
| `mise run test`                     | 124 simulator tests, Go race-enabled tests, broker persistence, gateway integration, and container builds/datasets/quarantine recovery passed |

The initial sandboxed Go run could not use the tool caches. After cache access
was approved, compilation exposed a local error-variable type mismatch, which
was corrected before the passing runs. The first root check found table
formatting; the repository formatter corrected it. Hosted CI has not run for
these local changes.

### Limits and next boundary

Evidence covers local Linux filesystems and graceful restarts, not power loss,
other host platforms, sustained load, or storage exhaustion. File and directory
sync plus atomic publication are required of the configured storage. Context
deadlines are checked between filesystem operations and cannot interrupt a
blocked kernel filesystem call. Quarantine has no eviction or replay tooling;
operators retain its directory/volume and provision capacity. Source metadata
on invalid records remains untrusted, and repeated invalid attempts can create
multiple records.

Valid deliveries reach the handler, but the command still returns
`ErrNoDisposition` there until P02-005 supplies the internal stream sink.
Quarantine failure leaves a delivery pending until reconnection/restart rather
than retrying disposition on the same connection. No enrollment lookup,
deduplication, clock-skew cutoff, or universal physical range was introduced.

## Go engineering review follow-up — 2026-10-28

Reviewed all Go source and tests using the maintainer's `go-engineering` skill,
including module/workspace requirements, build tags, CI tasks, accepted
contracts, and the resolved Eclipse Paho v0.23.0 source. The maintainer had
accepted and committed the initial P02-004 implementation as `0d9f0bb` before
this review.

Three corrections were warranted:

- Paho advertises `MaximumPacketSize` but its incoming reader does not enforce
  that property before allocation. Added a connection wrapper that checks the
  MQTT fixed header and remaining length before exposing the frame to Paho,
  then streams each permitted body. Tests cover fragmented headers, multiple
  frames, exact limits, malformed/truncated lengths, and an oversized CONNACK
  whose body is never sent. The scripted peer confirms rejection without
  waiting for the operation timeout.
- `New` copied configuration values but retained caller-owned pointers to
  measurement bounds. It now copies the pointed-to values too. A regression
  mutates all three original bounds after construction and verifies that the
  gateway continues using its validated policy. Documented the gateway's Run
  and counter concurrency contracts.
- Quarantine failures now identify the failed operation and preserve the
  underlying error through wrapping. Cleanup closes an incomplete record once
  and reports temporary-file cleanup errors alongside the primary failure.
  A failed serialization test verifies temporary-file removal and preservation
  of the marshaler error; the missing-directory case verifies its filesystem
  cause remains inspectable.

`mise run gateway:test` passed with the race detector. `mise run gateway:check`
passed formatting, vet, build, and dependency checksum verification.
`mise run gateway:test:integration` passed the existing real-broker
acknowledgement, quarantine outage/redelivery, and session-recovery assertions
with the new connection wrapper. `mise run fix` (including repository checks)
and `git diff --check` also passed. Evidence remains local Linux amd64; the
earlier durability and platform limitations still apply. No dependency or
toolchain requirement changed.

The ingestion specification and gateway guide now describe the enforced frame
limit. These corrections are a local review follow-up under #22, with commits
and publication remaining maintainer-owned.

## Weekly review

The gateway evidence now covers ingress validation and durable local invalid
disposition in addition to connection/session behavior. Internal publication,
consumer failure handling, and simulator-to-stream integration remain the next
capability boundaries; GitHub owns their delivery state.
