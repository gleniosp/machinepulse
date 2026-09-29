# ADR-0002 — Polyglot monorepo workspaces and task interface

- **Status:** Accepted
- **Date:** 2026-09-29
- **Updated:** 2026-09-29
- **Decision owners:** Project maintainer
- **Related requirements:** None directly
- **Related specifications:** [Developer tooling baseline](../developer-tooling.md), [Architecture overview](../architecture/overview.md), [Runtime boundaries](../architecture/runtime-boundaries.md)
- **Related experiments:** None
- **Supersedes:** None
- **Superseded by:** None

## Context

MachinePulse is expected to grow across Python simulation and analytics, Go
services, TypeScript applications, shared contracts, and infrastructure. These
components need to evolve together while keeping their dependency resolution,
builds, and tests understandable to developers familiar with each ecosystem.

The accepted [developer tooling baseline](../developer-tooling.md) already
assigns repository toolchain selection and common commands to mise, and assigns
package dependencies to native managers. Before this ADR, it did not establish
ecosystem workspaces or a consistent way to compose project-local tasks. This
decision fills that gap; the developer tooling baseline records the detailed
workspace and lockfile policy.

The project should organize code around applications, services, libraries,
contracts, and infrastructure. Language remains a project implementation
choice. Shared contracts should make cross-language dependencies visible and
support generated clients where appropriate. Add a second cross-repository
build graph only when a concrete need is measured.

## Decision

Adopt a polyglot monorepo with mise as the repository-level toolchain and task
interface. Keep dependency graphs, workspace manifests, lockfiles, and project
scripts in their native ecosystems. The [developer tooling baseline](../developer-tooling.md)
owns the detailed versions and command conventions.

### Repository organization

Organize projects by architectural responsibility. The intended top-level
areas are:

```text
apps/          # user-facing product applications
services/      # independently deployable runtime services
packages/      # reusable runtime libraries, SDKs, and components
contracts/     # OpenAPI, Protobuf, events, and shared schemas
infra/         # local runtime, deployment, and infrastructure definitions
tools/
  simulator/    # synthetic telemetry CLI and fixture generator
docs/
mise.toml
```

`apps/` contains user-facing product applications; `services/` contains
independently deployable runtime services. The simulator is an engineering
tool that generates synthetic telemetry and fixtures, so it belongs in
`tools/`, not in either runtime category. Create other areas as their projects
are added rather than creating empty directories. `packages/` is
language-neutral: a reusable Python package shared by Python services belongs
there just as a TypeScript package does. Contracts are versioned architectural
components; their changes should be checked for compatibility, with client or
model generation added where it helps consumers.

### Toolchain and task ownership

- Root mise configuration selects shared development tools and exposes the
  repository task interface. Pin supported versions through mise rather than
  relying on undocumented global installations.
- A project may have a small `mise.toml` for project-specific tools,
  environment variables, or mise task names. Root tool and environment
  settings are shared by default; project settings add to or override them only
  when needed.
- Each project owns its native scripts and tasks. JavaScript/TypeScript
  projects expose tasks through package scripts and pnpm; other projects use
  their ecosystem tooling. A project remains directly buildable and testable
  with its native commands.
- The root mise interface provides common commands such as `setup`, `dev`,
  `lint`, `test`, `build`, and `check`. These commands delegate to the
  corresponding tasks of projects that implement them, preserve failures, and
  provide a consistent local and CI entry point. Project-specific tasks remain
  addressable for targeted work. CI runs the root mise commands used by
  contributors. Configure project mise files as monorepo task roots and use
  path-aware task targets to compose the root aliases.

### Native workspaces and lockfiles

Each ecosystem manages its own dependency graph. Workspace roots may define
shared versions and common configuration; individual projects declare their
direct dependencies and native scripts. Each ecosystem retains the lockfile
shape required by its native workspace model, rather than forcing one lockfile
per project or a universal dependency model.

| Ecosystem | Workspace and shared configuration | Project-owned configuration |
|---|---|---|
| Python | A root `pixi.toml` workspace, shared settings, and a dependency pool where Pixi supports inheritance | Each project keeps package metadata and direct dependencies. Project task aliases live in its `mise.toml`; use the root workspace's shared environment and lockfile |
| JavaScript / TypeScript | A root pnpm workspace, catalogs for shared version ranges, and one workspace lockfile | Each package keeps its `package.json`, direct dependencies, and scripts |
| Go | A root `go.work` coordinates local Go modules | Each module keeps its own `go.mod`, `go.sum`, and Go commands |
| Rust, JVM, and future ecosystems | Use the ecosystem's native workspace or multi-project feature when introduced | Projects keep native manifests, scripts, and lockfiles according to that workspace model |
| Infrastructure | Keep infrastructure dependencies and provider configuration in their own area | Use native provider lockfiles and named mise tasks |

Pixi's shared dependency pool applies only to dependency tables supported by
Pixi's workspace model. In particular, PyPI dependencies remain declared by
the projects that use them. pnpm catalogs centralize shared version ranges;
they do not remove each package's responsibility to declare what it uses. Go
workspace coordination does not replace each module's own manifest or sum
file.

### Repository evolution and automation

- Use native workspaces and mise for workspace management and task
  orchestration.
- Consider Nx later only if measured repository needs exceed the native setup,
  such as excessive CI work on unaffected projects, difficult cross-language
  impact analysis, duplicated task-graph logic, or material caching benefits.
  If added, Nx sits above mise and native tools as an optimization layer;
  projects remain independently usable without Nx.
- Use Renovate for repository-wide dependency update proposals across native
  package manifests, containers, CI actions, and infrastructure providers.
  Group updates when related versions should be reviewed atomically, while
  leaving resolution to each ecosystem's package manager.
- Use ecosystem-native caches in CI. Avoid custom shell or CI logic that
  recreates dependency graphs, affected-project detection, or task caching.

## Alternatives considered

### Nx as a cross-project orchestrator

Nx offers a cross-project task graph, affected-project selection, and caching.
Adding it without a demonstrated graph or CI scaling problem would introduce
another abstraction. Use mise with native workspace capabilities unless
measured needs justify Nx.

### One package manager or lockfile for every language

A universal dependency model would obscure ecosystem-specific resolution and
build behavior, and would not replace native tools developers need for each
language. Keep separate dependency graphs and lockfile strategies per
ecosystem.

### Language-first top-level layout

Grouping all Python, Go, or TypeScript code together would make architectural
boundaries and deployable units less visible. Group projects by responsibility
and let each project choose its implementation language.

### Custom shell or CI orchestration

Hand-written dispatch scripts can gradually become a repository-specific build
system with duplicate dependency and impact logic. Use mise as the common task
entry point and keep project execution in native tooling.

### Separate repositories

Separate repositories would make contract, service, client, and infrastructure
changes harder to review atomically. Keep related product components together
while preserving their native project boundaries.

## Consequences

### Positive

- Contributors get one pinned toolchain setup and a stable repository command
  vocabulary.
- Native package managers remain usable from their own project directories.
- Shared dependencies and cross-project relationships can be declared in
  ecosystem workspaces without introducing a universal dependency resolver.
- Architecture and contracts are visible in repository layout, and related
  cross-stack changes can be reviewed atomically.
- Orchestration complexity can grow in response to measured repository needs.

### Negative or accepted trade-offs

- Contributors and CI must understand more than one ecosystem's manifests and
  lockfile behavior.
- Common task names have to be defined by convention, and some projects may
  not implement every task.
- Root workspaces establish lockfile ownership for their ecosystems and may
  require standalone projects to reconfigure their lockfiles and environments
  when they join a workspace.
- Shared workspace dependency features have ecosystem-specific limits; a
  shared version catalog does not mean every dependency declaration is
  centralized.
- mise task aggregation and explicit project registration require care as
  projects are added, so task coverage should remain visible and failures must
  not be hidden.

## Validation

Validate that:

- a clean checkout installs pinned tools through mise and dependencies through
  the appropriate native workspace;
- each project can run its own native setup, lint, test, build, and check tasks
  where those tasks apply;
- root `mise run` commands reach the corresponding project tasks and return a
  failure when any selected project task fails;
- CI uses the same root commands as local development; and
- adding a project in an existing ecosystem does not require changes to
  unrelated dependency manifests.

Revisit the orchestration choice if measured CI cost, project selection, or
cross-language dependency management becomes difficult to handle with mise and
native workspaces.

## References

- [mise monorepo tasks](https://mise.jdx.dev/tasks/monorepo.html)
- [Pixi workspaces](https://pixi.prefix.dev/latest/build/workspace/)
- [Pixi workspace dependencies](https://pixi.prefix.dev/latest/build/workspace_dependencies/)
- [pnpm workspaces](https://pnpm.io/workspaces)
- [pnpm catalogs](https://pnpm.io/catalogs)
