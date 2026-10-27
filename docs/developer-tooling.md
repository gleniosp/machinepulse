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

| Area                                 | Owner and expected files                                                                                                                                                                                                              | Repository-level integration                                                                       |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Shared tools and commands            | `mise.toml`, `mise.lock`, `prek.toml`, and root mise tasks                                                                                                                                                                            | Root tasks are the shared command interface                                                        |
| Go service or library                | A root `go.work` coordinates local modules; each module owns `go.mod` and `go.sum`                                                                                                                                                    | Add the Go toolchain through mise when Go code is introduced; project tasks delegate to the module |
| Python tool, app, or library         | Root Pixi workspace (`pixi.toml`, `pixi.lock`) owns the locked environment; root `ruff.toml` and `mypy.ini` own Python quality policy; each project owns package metadata, runtime dependencies, pytest configuration, and task names | Project mise tasks run native commands through the shared root Pixi environment                    |
| JavaScript/TypeScript app or package | Root pnpm workspace, catalog, and lockfile; each project owns its `package.json` dependencies and scripts                                                                                                                             | Package scripts run native tooling through pnpm                                                    |
| Infrastructure                       | `infra/` package or folder with Docker, database, and operational scripts                                                                                                                                                             | mise exposes documented infra tasks; services remain explicit and local-first                      |

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

The root mise config currently pins GitHub CLI, Go, Pixi, prek, and dprint. Python and its
environments come from the root Pixi workspace; Node.js and pnpm remain
unpinned until projects in those ecosystems need them. Exact versions and
dependency ranges belong in the manifests and lockfiles named in the ownership
table.

Pixi owns Python environment dependencies: the root manifest provides Python,
and its development feature provides Ruff, mypy, pytest, and Commitizen. The simulator's
`pyproject.toml` owns its package metadata, runtime dependencies, build settings,
and pytest configuration. Root `ruff.toml` and `mypy.ini` own shared lint,
formatting, and strict type-checking settings for Python 3.13, including
simulator import roots. Pixi manifests describe
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

For running the current components without a host development toolchain, use
the [Docker quickstart](guides/docker-quickstart.md). Mise remains the shared
contributor and CI task interface. The Pixi workspace locks Linux amd64/arm64,
macOS Intel/Apple Silicon, and Windows amd64 environments; dependency resolution
does not by itself establish runtime validation on every platform.

Run `mise run setup` from the repository root for a local setup. It installs
the locked mise tools, installs the Pixi development environment, downloads
the gateway Go dependencies, installs pinned dprint plugins, and installs the
managed Git pre-commit and commit-msg hooks. Each step is safe to repeat. Run
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
workflows. See the [contribution guide](../CONTRIBUTING.md#github-cli-optional) for authentication and
least-privilege token guidance.

Root mise tasks are the contributor and CI entry points; project-specific
tasks and native commands remain in each project's configuration. Use
`mise tasks` to see the commands currently implemented. The repository check
task must propagate project failures instead of silently skipping required
checks. Root verbs such as `format`, `test`, and `check` apply to all current
projects; use `mise run simulator:<task>` or `mise run gateway:<task>` to target
a project directly.
The simulator CLI is owned by its project task and exposed from the root as
`mise run simulator:run`; its command-line arguments are forwarded unchanged,
and input/output paths resolve from the repository root.
All simulator project tasks also run from the repository root and address
project files through `tools/simulator/` paths, keeping direct and root-alias
invocations consistent.
`mise run pixi:lock-check` verifies that the root Pixi lockfile is current.
Pre-commit hooks run shared Python checks when Python files, Python manifests,
or mise task definitions change. Simulator tests run when simulator files or
root Pixi manifests change; the Pixi lock check runs when Pixi manifests or
simulator package metadata change. Gateway checks run
when the gateway module, Go workspace, or shared mise toolchain changes.
`mise run hooks:check` applies the configured hooks across all eligible
tracked repository files at the pre-commit stage. It does not validate a Git
commit-message file; that uses the separate commit-msg stage described below.

The [local infrastructure guide](../infra/README.md) owns Docker/Compose host
prerequisites and broker lifecycle commands. `mise run infra:check` validates
both the infrastructure-only and root application Compose configurations,
including the simulator profile, without a daemon. It is included in the root
`check` task and runs in pre-commit when infrastructure, root Compose files,
the Docker build-context filter, or root tasks change.
`mise run infra:test` proves broker persistence with disposable services and
is included in root `test`; it requires a running Docker daemon. Broker data
and image pins remain owned by `infra/`.

`mise run containers:test` builds and verifies the complete current Docker
workflow in a disposable project and is also included in root `test`.
The [Docker verification guide](guides/docker-quickstart.md#repeatable-verification)
owns its direct Bash command, isolation, cleanup, and evidence limits.

### Container test scripts

Docker Compose files, image recipes, and smoke tests live in `infra/docker/`.
The root `compose.yaml` remains the application entry point. The broker-only
environment is `infra/docker/compose.yaml`, tested by `broker-smoke-test.sh`;
`smoke-test.sh` tests the application images and runtime together.

The Bash wrappers run on the host. `verify-smoke.py` runs only inside the
simulator container with its locked Python 3.13 runtime and read-only test
mounts. It does not need a host Python installation to execute the smoke test.
Host-side contributor checks use pinned Ruff and mypy from the root Pixi
`dev` environment; they analyze the helper without executing it:

```sh
mise run python:check
mise run python:format
mise run containers:check
```

Root `ruff.toml` and `mypy.ini` own the shared lint, format, and strict
type-checking policy. Ruff scans the repository with its standard exclusions
plus `.pixi`;
mypy checks the source directories listed in that config, currently simulator
sources, tests, experiments, and Docker helpers. Add new Python source areas
to mypy's `files` list when introducing them. Component commands use the same
root policy while narrowing their targets. Keep exceptions scoped to modules
and justified; do not duplicate the shared settings in package configs.

`python:check` runs in root `check`, the shared Python pre-commit hook, and CI
through `hooks:check`. Root `format`, `format-check`, `lint`, and `typecheck`
cover the helper too. `containers:check` separately checks Bash syntax without
starting services; it also runs in root `check` and its scoped pre-commit hook.
VS Code selects Ruff for Python and prefers repository configuration. Use the
Pixi `dev` interpreter for editor analysis, as with the simulator.

## Formatting and editor support

Use `mise run format` to apply formatting and `mise run format-check` to check
it without editing files. Dprint owns Markdown, JSON/JSONC, YAML, and TOML;
Ruff owns Python and gofmt owns Go. Root `check`, the scoped document pre-commit
hook, and CI run the same `documents:format-check` task. Pre-commit reports
document formatting failures; run `mise run documents:format`, review, and
restage the result. No formatter automatically stages changes.

`dprint.json` owns coverage, generated/cache/lockfile/test-fixture exclusions, and versioned
plugin URLs with SHA-256 checksums. `mise run format:setup` installs the plugins;
the normal setup and CI call it. The Markdown plugin preserves prose line breaks
and code blocks; the Oxc plugin handles configuration files with embedded
language formatting disabled. These choices keep executable examples and other
language formatters under their existing owners. Update plugin URLs and
checksums together when upgrading. Dprint and its plugins are MIT-licensed
development tools, obtained from their upstream release URLs in the tool lock
and formatter config.

`.editorconfig` supplies UTF-8, LF, final-newline, whitespace, and indentation
defaults only for files without a dedicated formatter, including shell scripts,
Dockerfiles, plain text, and repository dotfiles. It does not override Go's tab
indentation or the dedicated document/Python formatters.

VS Code's workspace recommendations cover Python/Ruff, Go, dprint, EditorConfig,
YAML/TOML language support, Container Tools, and Oxc for the planned frontend.
VS Code already includes TypeScript/React language support. Recommending the
frontend extension does not introduce a frontend toolchain; its lint policy
belongs to the future package configuration. Workspace settings select the
owning formatter for current file types and disable the YAML/TOML extensions'
competing formatters. Launch VS Code from a mise-enabled shell so its extensions
find the repository-selected tools. Continue using the Pixi `dev` interpreter
for Python analysis.

## Commit-message validation

The [working agreement](working-agreement.md#git-and-repository-hygiene) owns
branch and Conventional Commit policy. `.cz.toml` selects Commitizen's
Conventional Commits implementation; Commitizen and its dependencies are locked
in the existing Pixi `dev` environment. Commitizen is an MIT-licensed development
dependency from [its upstream project](https://github.com/commitizen-tools/commitizen).

Prek passes Git's message filename to `mise run commit:check`, which delegates
to the Pixi `commit-check` task. To validate a prepared message without making
a commit:

```sh
mise run commit:check /path/to/commit-message.txt
mise exec -- prek run commit-check --hook-stage commit-msg --commit-msg-filename /path/to/commit-message.txt
```

Setup installs both Git hook stages. Ordinary file hooks run only at pre-commit;
Commitizen runs at commit-msg and propagates invalid-message failures. Empty
messages are allowed through this hook so Git can abort the commit normally.
Git-generated messages beginning with `Merge ` are permitted. Reverts use
`revert: ...`; ordinary Git `Revert "..."` subjects and `fixup!`, `squash!`, or
`amend!` subjects are rejected and need a Conventional Commit subject before
commit. Scoped subjects and actual breaking-change notation are supported.
The checker validates syntax; maintainers review whether the type, description,
and breaking-change claim accurately describe the change.

`mise run tooling:test` checks valid/invalid messages through both the task and
an installed commit-msg hook, using a filename containing spaces. It verifies
installation of both hook stages in a disposable repository, propagates
validation failures, and creates no commits. It also verifies dprint's file
coverage, exclusions, read-only failure behavior, and repeatable formatting in
disposable fixtures. Root `check` and CI run this regression check.

## Dependency and lockfile policy

- Commit the root mise and Pixi lockfiles with their workspace manifests.
- Keep each ecosystem's workspace lockfile at its workspace root; project
  manifests continue to declare their direct dependencies.
- Keep development tools out of runtime-only environments.
- Keep the mise-selected Pixi version, workspace `requires-pixi` minimum and
  upper bound, and simulator Docker build image compatible. Update the Docker
  image's digest with its version; verify locked installs after upgrades.
- Store infrastructure image references, Compose files, and database setup
  scripts under `infra/` and validate them through named mise tasks.
- Do not use a global developer installation as an undocumented dependency of
  a local or CI check.

## CI expectations

CI should install from committed lockfiles, run the same root mise checks used
by contributors, and publish enough output to diagnose failures. The active
check set grows with the projects in the repository; implementation status and
remaining readiness work is tracked through [GitHub milestones](https://github.com/gleniosp/machinepulse/milestones) and
[readiness checklist](project-readiness.md).
The [GitHub Actions workflow](../.github/workflows/pr-checks.yml) runs
on pull requests targeting `main`. It installs the locked repository tools and
simulator environment and pinned Go dependencies, then runs
`mise run hooks:check`. It also runs broker persistence, gateway integration,
and container workflow verification with Docker. The result is informational for merging; requiring the status check is deferred until the
project begins accepting outside contributions. Track the remaining work and
PR evidence in
[P01-012](https://github.com/gleniosp/machinepulse/issues/93).

## Go gateway tasks

### Local environment defaults

Copy root `.env.example` to `.env` for local service configuration. Root mise
reads the optional file with its dotenv parser into template variables, then
exports the supported application settings while preserving values already
present in the caller's environment (including explicit empty values). This
mapping in root `mise.toml` is the list of supported local settings. Its path
is anchored to the root configuration, regardless of the project task's
working directory. Missing `.env` files do not block setup, checks, or tests.

Service binaries read environment variables directly and do not load dotenv
files. Deployment platforms supply those variables. The
[gateway guide](../services/telemetry-gateway/README.md#configuration) owns its
variable names, precedence, and required-value behavior. Tests inject their
own configuration; broker integration tests discover their disposable
endpoints rather than use developer service addresses or static test files.

### Commands

The [telemetry gateway](../services/telemetry-gateway/README.md) is the first
Go module, coordinated by root `go.work`. Its project mise tasks own formatting
with gofmt, vet, package compilation, module checksum verification, unit tests
with the race detector, and an explicit broker integration task. Root common
verbs include gateway checks; root `test` also includes the Docker integration
task. `mise run gateway:check` needs no broker; `mise run gateway:test:integration` creates and cleans up its own disposable broker.

## References

- [mise configuration and tasks](https://mise.jdx.dev/getting-started)
- [mise lockfiles](https://mise.jdx.dev/dev-tools/mise-lock.html)
- [Pixi workspaces](https://pixi.prefix.dev/latest/first_workspace/)
- [Pixi in `pyproject.toml`](https://pixi.prefix.dev/latest/python/pyproject_toml/)
- [Pixi multiple-package workspaces](https://pixi.prefix.dev/latest/build/workspace/)
- [Pixi lock files](https://pixi.prefix.dev/latest/workspace/lock_file/)
- [Vite+ getting started](https://viteplus.dev/guide)
- [Vite+ project-local CLI](https://viteplus.dev/guide/local-cli)
- [Vite+ checks](https://viteplus.dev/guide/check)
- [Vite+ configuration](https://viteplus.dev/config/)
- [pnpm catalogs](https://pnpm.io/catalogs)
