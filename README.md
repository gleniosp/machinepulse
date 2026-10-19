# MachinePulse

> [!WARNING]
> Heavy development: interfaces and setup may change, and things may break.
> The [roadmap](https://github.com/gleniosp/machinepulse/milestones) is only partly implemented.

MachinePulse is an open-source condition-monitoring platform for rotating
machinery, such as motors and pumps. The goal is to turn measurements like
vibration and temperature into evidence people can use to investigate machine
health and plan maintenance.

It starts with simulated measurements so the pipeline can be developed and
tested without physical sensors. Synthetic conditions and analytical results
are engineering evidence, not validated diagnoses.

## What works today

The **Python simulator** generates repeatable datasets with measurements,
separate labels describing the simulated conditions, and a manifest recording
how each run was produced. The **Go gateway** receives MQTT messages and records
source identity and receipt time. MQTT and Kafka run locally in Docker.

These pieces are not connected end to end yet: the simulator writes files
rather than publishing to MQTT. The gateway currently runs in **observation
mode**; it logs received messages but withholds acknowledgement because durable
storage/publication is not implemented. Its one-message receive limit then
pauses further deliveries. Kafka is available, but receives no gateway events yet.

The intended path is:

```text
Simulator / future sensors → MQTT → Go gateway → Kafka
  → storage and Python analytics → alerts and maintenance → API / dashboard
```

Storage, analytics, maintenance workflows, and the dashboard remain planned.
See the [architecture](docs/architecture/overview.md) for responsibilities and
the [GitHub milestones](https://github.com/gleniosp/machinepulse/milestones)
for implementation progress.

## Try it with Docker

From a checkout, use Docker with Compose **2.20.3+** and a running daemon.
Host Go, Python, mise, and GitHub authentication are not required. Commands use
Bash or Zsh; on Windows, use WSL2 with Docker Desktop integration.

On Linux, match generated-file ownership to your account first:

```sh
export MACHINEPULSE_UID=$(id -u)
export MACHINEPULSE_GID=$(id -g)
```

Generate a small example dataset from the repository root:

```sh
mkdir -p simulator-output
docker compose run --rm --build simulator
```

The command prints its output path under `simulator-output/`. Each run contains
`telemetry.jsonl` measurements, `ground-truth.jsonl` labels, and `manifest.json`
metadata. The first build downloads images and dependencies.

To start the brokers and gateway separately from dataset generation:

```sh
docker compose up --build --detach --wait --wait-timeout 180
docker compose logs --tail 50 gateway
# Look for mqtt_connected (and mqtt_subscribed for a new session).
docker compose down
```

Stopping preserves broker volumes and generated files. The
[Docker guide](docs/guides/docker-quickstart.md) covers configuration, resource
requirements, publishing a sample message, individual components, and checks.

## Delivery and recovery

- **Duplicates:** MQTT QoS 1 allows repeated delivery (at least once). Source
  event IDs are preserved; consumer deduplication and safe repeated side effects
  (idempotency) are planned, not implemented.
- **Ordering:** producer timestamps remain separate from gateway receipt time.
  The design assumes late or out-of-order messages and sequence gaps.
- **Failures:** gateway reconnect and pending-message redelivery are tested
  while the MQTT session survives. Durable quarantine, downstream retries,
  replay, and producer buffering remain planned; session persistence alone
  does not guarantee data retention.

The [ingestion contract](docs/specs/ingestion.md) and
[data-flow design](docs/architecture/data-flow.md) explain these boundaries.
There is no end-to-end exactly-once guarantee or production-readiness claim.

## Development and contribution

Use the [mise development setup](docs/developer-tooling.md#root-setup-and-tasks)
for editing and checks. Development is maintainer-led; read the
[provisional contribution guide](CONTRIBUTING.md) before proposing substantial
work. The [documentation hub](docs/README.md) provides technical context;
[GitHub issues](https://github.com/gleniosp/machinepulse/issues) track implementation.

Licensed under [Apache-2.0](LICENSE).
