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
| Go service or library | Root `go.work` coordinates local modules; each module owns `go.mod` and `go.sum` | mise supplies the selected Go toolchain; project tasks delegate to the module |
| Python service or ML/data package | Root Pixi workspace (`pixi.toml`, `pixi.lock`) owns shared settings and supported shared dependency specs; each project keeps its package metadata and Pixi environment/tasks | mise supplies the pinned Pixi CLI; Pixi owns Python dependency resolution and execution through `pixi run --locked` |
| JavaScript/TypeScript app or package | Root `pnpm-workspace.yaml` and `pnpm-lock.yaml`; catalogs hold shared version ranges; each project owns `package.json` dependencies and scripts | mise supplies Node and pnpm; package scripts delegate to native tools such as Vite+ where selected |
| Infrastructure | `infra/` package or folder with Docker, database, and operational scripts | mise exposes documented infra tasks; services remain explicit and local-first |

Pixi environments may use conda-forge packages, PyPI packages, or both where
appropriate for the Python component. Pixi workspace dependency sharing is
limited to the dependency tables supported by Pixi; PyPI dependencies stay
declared by the projects that use them. A Python component must document the
source and licensing of non-standard datasets, models, or binary artifacts it
uses. Reusable runtime libraries in any language belong in `packages/`; use
`tools/` for repository tooling and generators. The `infra/` area must not
introduce hidden external services or require credentials for the Phase 01
local workflow.

## Proposed toolchains

These are the proposed initial baselines. Exact patch versions and lockfile
entries belong in the implementation phase once each package exists.

| Area | Proposed baseline | Decision state |
|---|---|---|
| Repository manager | mise | Maintainer direction; record a supported minimum version when `mise.toml` is added |
| Repository Git hooks | prek, installed through mise | Maintainer direction; start with prek's native hooks and extend as project checks grow |
| Go | Go 1.27.x | Proposed; select and lock the patch version in the Go module/CI setup |
| Python | Python 3.13.x in Pixi environments | Selected for the simulator; evaluate 3.14.x separately for the ML/data stack |
| Python dependency manager | Pixi 0.76.1, installed through mise | Pinned in the root `mise.toml`; the Pixi workspace owns its root `pixi.lock`, while projects own package metadata and environment/task definitions |
| Node.js | Node.js 24 LTS | Proposed; managed by mise, not by a global Vite+ environment |
| JavaScript package manager | pnpm 10.x | Maintainer direction; managed by mise and selected by the root workspace |
| Go formatting and checks | `gofmt`, `go vet`, and `golangci-lint` | Proposed baseline |
| Python formatting, linting, typing, and tests | Pixi development environment with Ruff, mypy, and pytest | Used by the simulator; runtime-only dependencies remain in its Pixi `default` environment |
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

The root `mise.toml` should provide a common repository task vocabulary:

```text
mise install --locked
mise run setup
mise run dev
mise run build
mise run format
mise run format-check
mise run lint
mise run typecheck
mise run test
mise run check
mise run hooks:install
mise run hooks:check
```

Project `mise.toml` files and native manifests own project-specific task
definitions. Root mise tasks compose the corresponding tasks for projects that
implement them, preserve failures, and make the selected project set visible.
Do not silently report success for a missing required check. Add `dev` and
`build` delegates as projects define those actions. The current simulator
delegates its Python checks through Pixi. CI uses the same root commands that
contributors run locally. Expected native commands include:

```text
go fmt ./...
gofmt -l .
go vet ./...
golangci-lint run

pixi run --locked -e dev format
pixi run --locked -e dev lint
pixi run --locked -e dev typecheck
pixi run --locked -e dev test

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
- Commit one root `pixi.lock` for the Pixi workspace; project manifests own
  package-specific dependencies and environments. CI uses `pixi run --locked`
  or the equivalent locked installation mode. Use development environments
  for tests and quality checks; keep development tools out of runtime-only
  environments.
- Commit the root `pnpm-lock.yaml` for the pnpm workspace; each package keeps
  its own `package.json`. CI uses `pnpm install --frozen-lockfile`.
- Add root `go.work` when the first Go module is introduced. Each Go module
  keeps its own `go.mod` and `go.sum` and remains directly testable with Go.
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
- Implement the accepted [ADR-0002](adr/0002-polyglot-monorepo-workspaces.md)
  through [P01-010](tasks/phase-01-simulated-world.md#p01-010--establish-the-polyglot-workspace-and-mise-task-interface),
  before Phase 02 introduces the Go service.
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
