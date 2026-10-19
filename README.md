# MachinePulse

MachinePulse is an open-source, simulation-first condition-monitoring platform
for rotating machinery.

## Quick start

Install [mise](https://mise.jdx.dev/) and Docker with Compose (see the
[infrastructure prerequisites](infra/README.md#prerequisites-and-start)), then
run these commands from the repository root:

```sh
cp .env.example .env
mise run setup
mise run check
```

`setup` installs the locked tools, Python environment, and Go dependencies, then configures the
pre-commit hook. `check` runs the checks currently available in the repository.
See the [developer tooling baseline](docs/developer-tooling.md) for the command
interface and ownership details.

The root `.env` supplies local service configuration through mise. Existing
environment variables take precedence. The gateway guide documents
[configuration and deployment](services/telemetry-gateway/README.md#configuration).

## Contributing

Development is maintainer-led and interfaces are changing quickly. See the
[provisional contribution guide](CONTRIBUTING.md) before starting work.
Trying the project locally does not require GitHub authentication.

## Project documentation

The end-to-end monitoring workflow is not available yet. See:

- [Simulator quickstart](docs/guides/simulator-quickstart.md) — generate a
  small local dataset and understand its files.
- [Local telemetry infrastructure](infra/README.md) — start and verify the
  local MQTT broker and Kafka stream.
- [Telemetry gateway](services/telemetry-gateway/README.md) — receive local
  MQTT telemetry and verify delivery recovery.
- [Documentation hub](docs/README.md) — document map and current project status.
- [Product vision](docs/product/vision.md) — purpose, users, and principles.
- [Product scope](docs/product/scope.md) — version 0.1 boundaries and non-goals.
- [Architecture overview](docs/architecture/overview.md) — system shape and evolution.
- [Project governance](docs/project-governance.md) — contribution, security, and provenance guidance.
