# ADR-0002 — Polyglot monorepo workspaces and task interface

- **Status:** Accepted
- **Date:** 2026-09-29
- **Updated:** 2026-09-29
- **Decision owners:** Project maintainer
- **Related requirements:** None directly
- **Related specifications:** [Developer tooling baseline](../developer-tooling.md), [Architecture overview](../architecture/overview.md), [Runtime boundaries](../architecture/runtime-boundaries.md)
- **Related experiments:** None
- **Related tasks:** [P01-010 — Establish the polyglot workspace and mise task interface](../tasks/phase-01-simulated-world.md#p01-010--establish-the-polyglot-workspace-and-mise-task-interface)
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
root workspaces for Pixi and pnpm, or a consistent way to compose
project-local tasks. This decision fills that gap; the updated developer
tooling baseline records the detailed workspace and lockfile policy.

The project should organize code around applications, services, libraries,
contracts, and infrastructure. Language remains a project implementation
choice. Shared contracts should make cross-language dependencies visible and
support generated clients where appropriate. The initial repository size does
not justify adding a second cross-repository build graph before a concrete need
is measured.

## Decision

Adopt a polyglot monorepo with mise as the repository-level toolchain and task
interface. Keep dependency graphs, workspace manifests, lockfiles, and project
scripts in their native ecosystems. The maintainer accepted this decision on
2026-09-29. Its detailed developer-tooling conventions are maintained in the
[developer tooling baseline](../developer-tooling.md), and implementation is
tracked by P01-010.

### Repository organization

Organize projects by architectural responsibility. The intended top-level
areas are:

```text
apps/       # user-facing applications
services/   # independently deployable services
packages/   # reusable runtime libraries, SDKs, and components in any language
contracts/  # OpenAPI, Protobuf, events, and shared schemas
infra/      # local runtime, deployment, and infrastructure definitions
tools/      # repository tooling and generators
docs/
mise.toml
```

This is a target organization, not a required bulk move of existing files.
Projects move when a scoped implementation task needs the new boundary.
`packages/` is language-neutral: a reusable Python package shared by Python
services belongs there just as a TypeScript package does. Each package keeps
its native manifest and tooling. `tools/` is for repository and development
tools such as generators, not reusable runtime libraries. Contracts are
versioned architectural components; their changes should be linted and
checked for compatibility, with client or model generation added where it
helps consumers.

### Toolchain and task ownership

- The root `mise.toml` and `mise.lock` select and install shared development
  tools, including Pixi, Node.js, pnpm, and prek. Add Go and other ecosystem
  toolchains there as their projects are introduced. Pin supported versions
  through mise rather than relying on undocumented global installations.
- A project may have a small `mise.toml` for project-specific tools,
  environment variables, or mise task names. Root tool and environment
  settings are shared by default; project settings add to or override them only
  when needed.
- Each project owns its native scripts and tasks. Python projects expose tasks
  through Pixi, JavaScript/TypeScript projects through package scripts and
  pnpm, and other projects through their ecosystem tooling. A project remains
  directly buildable and testable with its native commands.
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
| Python | A root `pixi.toml` workspace, shared workspace settings, and a dependency pool where Pixi supports inheritance | Each Python project keeps its own package metadata, direct dependencies, environments, and Pixi tasks; the workspace lockfile is committed at the workspace root |
| JavaScript / TypeScript | A root `pnpm-workspace.yaml`, pnpm catalogs for shared version ranges, and the root workspace lockfile | Each package keeps its `package.json`, direct dependencies, and scripts |
| Go | A root `go.work` coordinates local Go modules | Each module keeps its own `go.mod`, `go.sum`, and Go commands |
| Rust, JVM, and future ecosystems | Use the ecosystem's native workspace or multi-project feature when introduced | Projects keep native manifests, scripts, and lockfiles according to that workspace model |
| Infrastructure | Keep infrastructure dependencies and provider configuration in their own area | Use native provider lockfiles and named mise tasks |

Pixi's shared dependency pool applies only to dependency tables supported by
Pixi's workspace model. In particular, PyPI dependencies remain declared by
the projects that use them. Pin a Pixi release that supports the required
workspace features, and verify the actual project and environment layout when
the root workspace is introduced. pnpm catalogs centralize shared version
ranges; they do not remove each package's responsibility to declare what it
uses. Go workspace coordination does not replace each module's own manifest or
sum file.

### Repository evolution and automation

- Do not introduce Nx initially. Native workspaces and mise provide the
  starting developer interface and task orchestration.
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

### Nx as the initial orchestrator

Nx offers a cross-project task graph, affected-project selection, and caching.
Starting with it would add another abstraction before the repository has
demonstrated a graph or CI scaling problem. Defer it and use mise with native
workspace capabilities first.

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
- Root workspaces change lockfile ownership for Python and JavaScript. Moving
  the existing standalone simulator into the Pixi workspace requires lockfile
  and environment reconfiguration.
- Shared workspace dependency features have ecosystem-specific limits; a
  shared version catalog does not mean every dependency declaration is
  centralized.
- mise task aggregation and explicit project registration require care as
  projects are added, so task coverage should remain visible and failures must
  not be hidden.

### Follow-up work

- Add the required root workspace files and mise task configuration through
  P01-010; migrate the current simulator only as part of that scoped change.
- Pin mise-managed Pixi, Node.js, pnpm, prek, and later ecosystem tools; commit
  the root mise lockfile and set the supported minimum mise version.
- Verify shared dependency behavior and per-project tasks with the selected
  Pixi and pnpm versions, then record clean-checkout CI evidence.
- Add contract linting, compatibility checks, and code generation when the
  first cross-language contracts and consumers are implemented.
- Revisit Nx only when CI timing, affected-project selection, dependency
  tracing, or cache measurements demonstrate a gap.

## Validation

P01-010 validates the workspace and lockfile behavior against the pinned
versions and existing simulator project. The implementation should verify
that:

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
