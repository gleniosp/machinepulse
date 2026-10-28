# Run with Docker

Use Docker Engine or Docker Desktop with Compose 2.20.3 or newer and a running
daemon. Go, Python, Pixi, and mise are not required on the host. Run commands
from the repository root. Shell examples use Bash or Zsh; on Windows, use WSL2
with Docker Desktop integration. The first build downloads base images and locked
dependencies; allow the broker resources listed in the
[infrastructure guide](../../infra/README.md#prerequisites-and-start).

## Generate a dataset

Create the host output directory, then run the simulator:

```sh
mkdir -p simulator-output
docker compose run --rm --build simulator
```

The default command generates the small normal, imbalance, and overheating
example. It prints the output path; each invocation creates a new timestamped
directory under `simulator-output/` on the host. Each run contains
`telemetry.jsonl`, `ground-truth.jsonl`, and `manifest.json`. The
[simulator guide](simulator-quickstart.md#inspect-the-output) explains these
files and the limits of the synthetic conditions.

On Linux, Compose uses user/group `1000:1000` for the simulator. If your account
differs, run these before generation (or set the corresponding values in `.env`):

```sh
export MACHINEPULSE_UID=$(id -u)
export MACHINEPULSE_GID=$(id -g)
```

Create the output directory yourself so it belongs to your account. Docker
Desktop users can use the default settings. The simulator has no broker
dependency and exits when generation finishes; it does not publish to MQTT.

## Start the current runtime

```sh
docker compose up --build --detach --wait --wait-timeout 180
docker compose ps
docker compose logs --tail 50 gateway
```

This starts MQTT, Kafka, and the gateway. The simulator is an on-demand tool
and does not start with `up`. Broker health checks establish availability;
the gateway currently has no health endpoint. Look for `mqtt_subscribed` and
`mqtt_connected` in its logs to confirm its MQTT receive path is ready.

Publish the contract fixture with the broker's bundled client:

```sh
docker compose exec -T mqtt mosquitto_pub \
  -V mqttv5 -q 1 \
  -t machinepulse/v1/telemetry/01M000000028T5CY4GNF6YY4HM \
  -s < tools/simulator/tests/fixtures/telemetry.v1.json
docker compose logs --tail 50 gateway
```

Expect `telemetry_received` and `telemetry_unacknowledged`. The gateway validates
this valid fixture and preserves its bytes, then withholds acknowledgement until
the stream sink is implemented. Its one-message receive limit pauses subsequent
deliveries. Kafka is available locally, but the gateway does not publish to it
yet. See the [gateway guide](../../services/telemetry-gateway/README.md) for
the validation/quarantine example, configuration, and recovery behavior.
Invalid deliveries are recorded before acknowledgement in the persistent
`gateway-quarantine` volume. Publish invalid fixtures before a valid pending
delivery when exercising this path on a fresh session.

Stop the runtime while preserving broker and quarantine data:

```sh
docker compose down
```

Later `up` commands reuse the broker and quarantine volumes. Dataset files remain on the host.
Broker persistence, connection addresses, and trusted-local-network limitations
are owned by the [infrastructure guide](../../infra/README.md).

## Configuration and individual components

The root `.env` is optional for Docker. Compose reads it for interpolation;
exported variables take precedence. `.env.example` lists supported overrides.
Compose explicitly points the gateway to `mqtt:1883` and uses a container
client ID distinct from the host gateway's ID. Host port overrides do not
change this internal address. Avoid running multiple gateways with the same
client ID.

The root Compose file includes the existing broker definitions. It uses the
same project name and volumes as the infrastructure-only commands. Use one
entry point at a time for lifecycle operations; `docker compose down` also
stops the brokers started through that project.

```sh
# Brokers only, using their existing configuration.
docker compose --file infra/docker/compose.yaml up --detach --wait

# Gateway and its MQTT dependency, without starting Kafka.
docker compose up --build --detach --wait gateway

# Build one application image independently.
docker compose build gateway
docker compose build simulator

# Inspect the simulator CLI without generating data (output directory required).
docker compose run --rm simulator --help
```

For a custom simulator configuration, mount it read-only and pass its container
path. Choose a fresh output subdirectory to preserve earlier runs:

```sh
docker compose run --rm \
  --volume "$PWD/tools/simulator/examples/runs.v1.json:/config.json:ro" \
  simulator generate --config /config.json --output-dir simulator-output/custom-run
```

The built images can also run independently of Compose. Supply a reachable
broker address to `machinepulse-gateway:local`; bind a writable directory to
`/output/simulator-output` for `machinepulse-simulator:local`. The images do not
contain host configuration, Git metadata, or a Docker socket. Remote deployment
security and operations are outside this local workflow.

## Platforms and provenance

The shared Pixi workspace locks dependencies for Linux amd64/arm64, macOS
Intel/Apple Silicon, and Windows amd64. Containers use Linux images; Docker
Desktop supplies the Linux runtime on macOS and Windows. Both image recipes
support Linux amd64 and arm64. Native runtime evidence is recorded in the
[engineering notes](../journal/public-onboarding.md); a resolved lockfile or
successful cross-build alone does not establish runtime testing on every host.

Pixi installs the simulator's locked `default` environment during the build;
the runtime image contains Python and runtime dependencies without Pixi or
development tools. Base images are pinned by version and digest under
`infra/docker/`. The gateway uses its pinned Go module and a static binary.

Git metadata is excluded from image builds. Simulator manifests therefore
record a null revision unless one is supplied at build time:

```sh
export MACHINEPULSE_CODE_REVISION=$(git rev-parse HEAD)
docker compose build simulator
```

Only use a revision that identifies the source being built. Container manifests
report `working_tree_dirty` as null because they cannot inspect the checkout.
The existing [mise development workflow](../developer-tooling.md) remains
available for editing, checks, and tests.

## Repeatable verification

```sh
bash infra/docker/smoke-test.sh
# Equivalent contributor task:
mise run containers:test
```

The host entry point, `infra/docker/smoke-test.sh`, requires Bash and Docker.
It mounts `verify-smoke.py` read-only and runs it inside the simulator image
with `/app/.pixi/envs/default/bin/python`: Python 3.13 from the shared Pixi
lockfile. The helper uses container-only paths and is not a host executable.
The separate `broker-smoke-test.sh` tests broker persistence without building
the applications.

The application smoke test builds both images without layer-cache reuse, compares two
generated datasets, checks valid/invalid reception, and verifies pending-message
recovery and quarantine persistence after gateway restart and full container recreation. Its separate
project, random host ports, temporary output, and image tags keep it independent
of the normal local runtime. It ignores the developer dotenv file, prints
service diagnostics on failure, and removes its own containers, volumes,
images, network, and temporary files on exit. Shared Docker build caches remain.

CI runs this test alongside the existing broker and gateway integration checks.
These checks demonstrate local validation, quarantine, and pending-message
recovery. Kafka publication and power-loss recovery remain unverified.

For editing these scripts, the pinned local lint/format commands are documented
in [developer tooling](../developer-tooling.md#container-test-scripts). Static
checks do not execute the Python evidence checker or start Docker services.

## References

- [Docker Compose include](https://docs.docker.com/compose/how-tos/multiple-compose-files/include/)
- [Pixi container deployment](https://pixi.prefix.dev/latest/deployment/container/)
