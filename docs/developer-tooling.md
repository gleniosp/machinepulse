# Developer Tooling and Validation Baseline

- **Status:** Accepted baseline
- **Related task:** P00-010; [P01-009](tasks/phase-01-simulated-world.md#p01-009--add-repository-hooks-for-baseline-checks)
- **Related phase:** [Phase 01 — Simulated industrial world](tasks/phase-01-simulated-world.md)
- **Related readiness gate:** [Pre-implementation readiness](project-readiness.md)

## Baseline policy

Use `mise` as the repository-level tool and task manager. It owns the shared
toolchain selection, environment entry points, and commands contributors and CI
run from the repository root. The dependency manager for each package, app,
service, or infrastructure area owns that area's dependencies and lockfile.

The repository should not create one undifferentiated environment for every
language. Root `mise.toml` and its committed lockfile coordinate the tools and
tasks; package manifests and lockfiles remain authoritative for package-level
dependencies. Tool versions should be pinned in implementation commits when
the corresponding package exists.

## Ownership model

| Area | Owner and expected files | Repository-level integration |
|---|---|---|
| Shared tools and commands | `mise.toml`, `mise.lock`, `prek.toml`, and root mise tasks | `mise install --locked` and `mise run <task>` |
| Go service or library | Its own `go.mod` and `go.sum` | mise supplies the selected Go toolchain; root tasks delegate to the module |
| Python service or ML/data package | Its own `pixi.toml` or `pyproject.toml` and `pixi.lock` | mise supplies Pixi and delegates through `pixi run --locked` |
| React/Vite frontend | Its own `package.json`, `pnpm-lock.yaml`, and `vite.config.ts` | mise supplies Node and pnpm; pnpm owns the local `vite-plus` package and its `vp` commands |
| Infrastructure | `infra/` package or folder with Docker, database, and operational scripts | mise exposes documented infra tasks; services remain explicit and local-first |

Pixi environments may use conda-forge packages, PyPI packages, or both where
appropriate for the Python component. A Python component must document the
source and licensing of non-standard datasets, models, or binary artifacts it
uses. The `infra/` area must not introduce hidden external services or require
credentials for the Phase 01 local workflow.

## Proposed toolchains

These are the proposed initial baselines. Exact patch versions and lockfile
entries belong in the implementation phase once each package exists.

| Area | Proposed baseline | Decision state |
|---|---|---|
| Repository manager | mise | Maintainer direction; record a supported minimum version when `mise.toml` is added |
| Repository Git hooks | prek, installed through mise | Maintainer direction; start with prek's native hooks and extend as project checks grow |
| Go | Go 1.27.x | Proposed; select and lock the patch version in the Go module/CI setup |
| Python | Python 3.13.x in Pixi environments | Proposed compatibility baseline; evaluate 3.14.x separately for the ML/data stack |
| Python dependency manager | Pixi | Maintainer direction; pin the CLI and commit each component's `pixi.lock` |
| Node.js | Node.js 24 LTS | Proposed; managed by mise, not by a global Vite+ environment |
| JavaScript package manager | pnpm 10.x | Maintainer direction; managed by mise and declared by each frontend package |
| Go formatting and checks | `gofmt`, `go vet`, and `golangci-lint` | Proposed baseline |
| Python formatting, linting, and tests | Pixi tasks using Ruff and pytest | Proposed baseline; mypy remains available for typed modules |
| TypeScript/React formatting and linting | Vite+ with Oxfmt and Oxlint | Maintainer direction; no default Prettier or ESLint dependency |
| TypeScript checks | Vite+ `vp check` with type-aware checking enabled | Proposed; verify against the first frontend package |
| TypeScript tests | Vite+ `vp test` backed by Vitest | Maintainer direction |

Vite+ is currently a beta, so the frontend package should keep its Vite+
configuration explicit and record the version used. The project can fall back
to the underlying Vite, Vitest, Oxlint, and Oxfmt commands if a Vite+ feature
blocks the implementation. This is a frontend toolchain choice, not a reason
to give Vite+ ownership of the repository's Node.js or pnpm environment.
The current Vite+ guidance expects Vite 8 or newer and Vitest 4.1 or newer;
verify those compatibility constraints when the frontend package is created.

Use the project-local Vite+ package through pnpm for frontend checks, for
example `pnpm exec vp check`. The repository does not need a globally installed
Vite+ CLI: mise remains responsible for Node.js and pnpm, while the frontend
package owns Vite+ through its package manifest and lockfile.

## Repository command contract

The root `mise.toml` should provide these commands once Phase 01 implementation
starts:

```text
mise install --locked
mise run format
mise run format-check
mise run lint
mise run typecheck
mise run test
mise run check
mise run hooks:install
mise run hooks:check
```

The root tasks should delegate to the components that exist in the current
phase. A task may be a no-op for an absent language area, but it must not hide a
failed check. Expected initial delegates are:

```text
go fmt ./...
gofmt -l .
go vet ./...
golangci-lint run

pixi run --locked format
pixi run --locked lint
pixi run --locked typecheck
pixi run --locked test

pnpm install --frozen-lockfile
pnpm exec vp fmt --check
pnpm exec vp lint
pnpm exec vp check --no-fmt --no-lint
pnpm exec vp test
```

The exact task graph belongs in `mise.toml` and the component manifests. For
example, a frontend package may use `vp check` as its combined format/lint/type
check, while a Python package may define its own Pixi tasks for the same
repository-level task names. CI must call the same root mise tasks contributors
run locally.

## Dependency and lockfile policy

- Commit `mise.lock` for repository-level tool resolution once the root
  configuration is introduced.
- Commit `go.mod` and `go.sum` with each Go module.
- Commit `pixi.lock` with each Pixi-managed Python component; CI uses
  `pixi run --locked` or the equivalent locked installation mode.
- Commit each frontend package's `pnpm-lock.yaml`; CI uses
  `pnpm install --frozen-lockfile`.
- Keep infrastructure image references, Compose files, and database migration
  or bootstrap scripts under `infra/` and validate them through named mise
  tasks.
- Do not use a global developer installation as an undocumented dependency of
  a local or CI check.

## CI expectations

The first CI workflow should:

1. run on pull requests and the default branch;
2. install the pinned repository tools with `mise install --locked`;
3. install component dependencies only from committed lockfiles;
4. run the root mise format, lint, type-check, unit, contract, and integration
   tasks that exist for the current phase;
5. fail on unsupported or untracked validation results; and
6. publish enough command output to diagnose failures.

Until runtime code and manifests exist, CI setup is a Phase 01 task rather than
a claim that these commands already pass in a clean checkout.

## Evidence boundaries

- Unit tests prove local domain behavior.
- Contract tests prove payload and boundary compatibility.
- Integration tests prove cooperating runtime components.
- End-to-end tests prove the monitored path across deployed boundaries.
- Load and failure tests support performance and resilience claims.

Do not substitute one evidence type for another or claim performance targets
before benchmarks exist.

## Open decisions and follow-ups

- Set and document the minimum supported mise version when the root
  configuration is created.
- Select exact toolchain patch versions and generate `mise.lock`.
- Confirm the Python 3.13/3.14 compatibility decision for the first Pixi
  environment and record the supported platforms/channels.
- Select the CI provider and runner image.
- Define the first `infra/` task surface for Docker and database checks.
- Add the root mise tasks as executable Phase 01 checks and record a
  clean-checkout run before the readiness gate is reopened for runtime work.
- Add the initial prek setup and native repository checks through [P01-009](tasks/phase-01-simulated-world.md#p01-009--add-repository-hooks-for-baseline-checks).

## References

- [mise configuration and tasks](https://mise.jdx.dev/getting-started)
- [mise lockfiles](https://mise.jdx.dev/dev-tools/mise-lock.html)
- [Pixi workspaces](https://pixi.prefix.dev/latest/first_workspace/)
- [Pixi lock files](https://pixi.prefix.dev/latest/workspace/lock_file/)
- [Vite+ getting started](https://viteplus.dev/guide)
- [Vite+ checks](https://viteplus.dev/guide/check)
- [Vite+ configuration](https://viteplus.dev/config/)
