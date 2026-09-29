# MachinePulse

MachinePulse is an open-source, simulation-first condition-monitoring platform
for rotating machinery.

## Quick start

Install [mise](https://mise.jdx.dev/) and run these commands from the repository
root:

```sh
mise run setup
mise run check
```

`setup` installs the locked tools and Python environment, then configures the
pre-commit hook. `check` runs the checks currently available in the repository.
See the [developer tooling baseline](docs/developer-tooling.md) for the command
interface and ownership details.

The end-to-end monitoring workflow is not available yet. See the
[documentation hub](docs/README.md) for project status. The simulator's intended
behavior and telemetry format are documented in the
[Simulator Behavior](docs/specs/simulator.md) and the
[telemetry contract](docs/specs/telemetry-contract.md).

## Project documentation

- [Documentation hub](docs/README.md) — document map and current project status.
- [Product vision](docs/product/vision.md) — purpose, users, and principles.
- [Product scope](docs/product/scope.md) — version 0.1 boundaries and non-goals.
- [Architecture overview](docs/architecture/overview.md) — system shape and evolution.
- [Project governance](docs/project-governance.md) — contribution, security, and provenance guidance.
