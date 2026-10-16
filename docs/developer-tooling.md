# Developer Tooling Baseline

- **Status:** Accepted baseline
- **Decision:** [ADR-0002 — Polyglot monorepo workspaces and task interface](adr/0002-polyglot-monorepo-workspaces.md)

## Baseline policy

Use `mise` as the repository-level tool and task manager. It owns the shared
toolchain selection, environment entry points, and commands contributors and CI
run from the repository root. The dependency manager for each package, app,
service, or infrastructure area owns that area's dependencies and lockfile.

The repository should not create one undifferentiated environment for every
language. Root `mise.toml` and `mise.lock` coordinate shared tools and commands;
native manifests and lockfiles remain authoritative for project dependencies
and tool-specific settings. Exact versions belong in those configuration files
and should not be repeated here.

## Ownership model

| Area | Owner and expected files | Repository-level integration |
|---|---|---|
| Shared tools and commands | `mise.toml`, `mise.lock`, `prek.toml`, and root mise tasks | Root tasks are the shared command interface |
| Go service or library | A root `go.work` coordinates local modules; each module owns `go.mod` and `go.sum` | Add the Go toolchain through mise when Go code is introduced; project tasks delegate to the module |
| Python tool, app, or library | Root Pixi workspace (`pixi.toml`, `pixi.lock`) owns the locked environment; each project owns package metadata, runtime dependencies, tool configuration, and task names | Project mise tasks run native commands through the shared root Pixi environment |
| JavaScript/TypeScript app or package | Root pnpm workspace, catalog, and lockfile; each project owns its `package.json` dependencies and scripts | Package scripts run native tooling through pnpm |
| Infrastructure | `infra/` package or folder with Docker, database, and operational scripts | mise exposes documented infra tasks; services remain explicit and local-first |

Pixi environments may use conda-forge packages, PyPI packages, or both where
appropriate for the Python component. Pixi workspace dependency sharing is
limited to the dependency tables supported by Pixi; PyPI dependencies stay
declared by the projects that use them. A Python component must document the
source and licensing of non-standard datasets, models, or binary artifacts it
uses. Reusable runtime libraries in any language belong in `packages/`; use
`tools/` for engineering tools and generators such as the simulator. The
`infra/` area must not introduce hidden external services or require
credentials for the local workflow.

## Toolchain policy

The root mise config currently pins GitHub CLI, Pixi, and prek. Python and its
environments come from the root Pixi workspace; Go, Node.js, and pnpm remain
unpinned until projects in those ecosystems need them. Exact versions and
dependency ranges belong in the manifests and lockfiles named in the ownership
table.

Pixi owns Python environment dependencies: the root manifest provides Python,
and its development feature provides Ruff, mypy, and pytest. The simulator's
`pyproject.toml` owns its package metadata, runtime dependencies, build settings,
and tool-specific pytest, Ruff, and mypy configuration. Pixi manifests describe
workspace environments and dependencies; they do not replace those tools'
configuration files.

## JavaScript/TypeScript workspace

When JavaScript/TypeScript code is introduced, add Node.js and pnpm through
mise and create one root pnpm workspace and lockfile. Define one named
`toolchain` catalog and declare each package's project-local `vite-plus`
dependency through `catalog:toolchain` in its initial `package.json`. Do not
install Vite+ globally; run its CLI through the package manager.

## Python project tasks

Pixi supports `[tool.pixi.tasks]` in `pyproject.toml`. Tasks belong to the Pixi
manifest selected for a command: the root workspace does not import task
definitions from a nested package manifest. In a multi-package workspace, the
root manifest owns workspace tasks and the member manifest describes its
package. The simulator's project-specific aliases therefore live in
`tools/simulator/mise.toml` and run native commands against the root Pixi
manifest, preserving its shared environment and lockfile.

## Root setup and tasks

Run `mise run setup` from the repository root for a local setup. It installs
the locked mise tools, installs the Pixi development environment, and installs
the managed Git pre-commit hook. Each step is safe to repeat. Run
`mise run hooks:install` separately only when the hook needs to be installed or
refreshed.

Task commands invoke selected tools directly through `mise exec -- <tool> ...`
(for example, `mise exec -- pixi ...`) so an earlier standalone executable on
`PATH` does not shadow the repository's selected tool. A nested shell may
resolve another copy from inherited `PATH`; if a tool is missing and mise's
auto-install is disabled, it may also fall back to `PATH`. The root
`.miserc.toml` excludes the named user-global mise config file from project
commands; this controls mise config loading, not `PATH` isolation.

Use the mise-managed GitHub CLI for repository issue and pull-request
workflows. See the [README](../README.md#github-cli) for authentication and
least-privilege token guidance.

Root mise tasks are the contributor and CI entry points; project-specific
tasks and native commands remain in each project's configuration. Use
`mise tasks` to see the commands currently implemented. The repository check
task must propagate project failures instead of silently skipping required
checks. Root verbs such as `format`, `test`, and `check` apply to all current
projects; use `mise run simulator:<task>` to target the simulator directly.
The simulator CLI is owned by its project task and exposed from the root as
`mise run simulator:run`; its command-line arguments are forwarded unchanged,
and input/output paths resolve from the repository root.
All simulator project tasks also run from the repository root and address
project files through `tools/simulator/` paths, keeping direct and root-alias
invocations consistent.
`mise run pixi:lock-check` verifies that the root Pixi lockfile is current.
Pre-commit hooks run file checks on eligible changed files, simulator checks
when simulator files or root Pixi manifests change, and the Pixi lock check
when Pixi manifests or simulator package metadata change.
`mise run hooks:check` applies the configured hooks across all eligible
tracked repository files.

The [local infrastructure guide](../infra/README.md) owns Docker/Compose host
prerequisites and broker lifecycle commands. `mise run infra:check` validates
the Compose configuration without a daemon; it is included in the root
`check` task and runs in pre-commit when infrastructure or root tasks change.
`mise run infra:test` proves broker persistence with disposable services and
is included in root `test`; it requires a running Docker daemon. Broker data
and image pins remain owned by `infra/`.

## Dependency and lockfile policy

- Commit the root mise and Pixi lockfiles with their workspace manifests.
- Keep each ecosystem's workspace lockfile at its workspace root; project
  manifests continue to declare their direct dependencies.
- Keep development tools out of runtime-only environments.
- Store infrastructure image references, Compose files, and database setup
  scripts under `infra/` and validate them through named mise tasks.
- Do not use a global developer installation as an undocumented dependency of
  a local or CI check.

## CI expectations

CI should install from committed lockfiles, run the same root mise checks used
by contributors, and publish enough output to diagnose failures. The active
check set grows with the projects in the repository; implementation status and
remaining readiness evidence belong in the [task plan](tasks/README.md) and
[readiness checklist](project-readiness.md).
The initial [GitHub Actions workflow](../.github/workflows/pr-checks.yml) runs
on pull requests targeting `main`. It installs the locked repository tools and
simulator environment, then runs `mise run hooks:check`. The result is
informational for merging; requiring the status check is deferred until the
project begins accepting outside contributions. Track the remaining work and
PR evidence in
[P01-012](tasks/phase-01-simulated-world.md#p01-012--run-repository-checks-on-pull-requests).

## References

- [mise configuration and tasks](https://mise.jdx.dev/getting-started)
- [mise lockfiles](https://mise.jdx.dev/dev-tools/mise-lock.html)
- [Pixi workspaces](https://pixi.prefix.dev/latest/first_workspace/)
- [Pixi in `pyproject.toml`](https://pixi.prefix.dev/latest/python/pyproject_toml/)
- [Pixi multiple-package workspaces](https://pixi.prefix.dev/v0.76.1/build/workspace/)
- [Pixi lock files](https://pixi.prefix.dev/latest/workspace/lock_file/)
- [Vite+ getting started](https://viteplus.dev/guide)
- [Vite+ project-local CLI](https://viteplus.dev/guide/local-cli)
- [Vite+ checks](https://viteplus.dev/guide/check)
- [Vite+ configuration](https://viteplus.dev/config/)
- [pnpm catalogs](https://pnpm.io/catalogs)
