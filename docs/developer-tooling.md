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

Root tasks are the contributor and CI entry points. `mise run check` calls
`format-check`, `lint`, and `typecheck` once each, followed by dependency,
lockfile, Compose, and shell-syntax checks. Type checking includes strict mypy
analysis of configured Python sources and compilation of the Go gateway.
`mise run test` owns unit and integration execution; checks never run tests.
Use `mise tasks` for the available commands or `simulator:<task>` and
`gateway:<task>` for project-specific work. Simulator commands run from the
repository root and forward CLI arguments unchanged.

The [local infrastructure guide](../infra/README.md) owns Docker/Compose host
prerequisites and broker lifecycle commands. `mise run infra:check` validates
both the infrastructure-only and root application Compose configurations,
including the simulator profile, without a daemon.
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
The root Python checks analyze the helper without executing it, using
`ruff.toml` and `mypy.ini`. Mypy covers simulator sources, tests, experiments,
and Docker helpers; add new Python source areas to its `files` list. Component
tasks narrow the targets while retaining this shared policy.
`mise run containers:check` checks Bash syntax without starting services.

## Formatting and editor support

Pre-commit invokes one `mise run fix` task: apply Ruff's safe fixes, run
`mise run format`, then run `mise run check`. Dprint owns Markdown, JSON/JSONC,
YAML, and TOML; Ruff owns Python and gofmt owns Go. Remaining violations require
manual changes. Prek also keeps case-conflict, merge-marker, and large-file
builtins, whose responsibilities are not provided by those formatters.
`mise run hooks:check` runs these hooks across tracked files and may apply fixes.

The pre-commit fix task covers eligible files repository-wide, including
untracked files. Prek temporarily stashes unstaged tracked edits when invoked
by Git and restores them afterward; follow its recovery instructions if fixes
conflict with those edits. Review any modified files and restage them before
retrying the commit. No formatter automatically stages changes.

`dprint.json` owns file coverage, exclusions, and the Oxc plugin URL/checksum.
`mise run format:setup` installs it during setup and CI. Oxc preserves prose line
breaks and disables embedded language formatting. Update its version and SHA-256
together. Dprint and Oxc are MIT-licensed development tools from the upstream
releases recorded in the tool lock and formatter config.

### Test fixtures

Dprint excludes `tools/simulator/tests/fixtures/**`.
`run-manifest.v1.json` and `ground-truth.v1.json` are exact serialized-output
goldens: [the reproducibility test](../tools/simulator/tests/test_reproducibility.py)
compares their text with compact, sorted-key JSON, ignoring only the final newline.
`vibration-window.v1.json` is a numerical golden compared as parsed JSON;
`telemetry.v1.json` and `telemetry-invalid/*.json` are contract inputs. Keep the
whole directory as test artifacts rather than applying source formatting.
Generated datasets under `simulator-output/` are excluded too.

### Editor support

`.editorconfig` supplies UTF-8, LF, final-newline, whitespace, and indentation
defaults only for files without a dedicated formatter, including shell scripts,
Dockerfiles, plain text, and repository dotfiles. It does not override Go's tab
indentation or the dedicated document/Python formatters.

Workspace settings select the owning formatters, enable document/configuration
format-on-save, and disable implicit Ruff fix/import save actions. Python and
Ruff use the Pixi `dev` environment. Launch VS Code from a mise-enabled shell so
dprint resolves to the selected binary. The recommendations in
`.vscode/extensions.json` complement VS Code's built-in TypeScript/React support.

## Commit-message validation

The [working agreement](working-agreement.md#git-and-repository-hygiene) owns
branch and Conventional Commit policy. `.cz.toml` selects Commitizen's
Conventional Commits implementation; Commitizen and its dependencies are locked
in the existing Pixi `dev` environment. Commitizen is an MIT-licensed development
dependency from [its upstream project](https://github.com/commitizen-tools/commitizen).

The separate commit-msg hook passes Git's filename through mise to Pixi's
`commit-check` task. To check a prepared message without committing:

```sh
mise run commit:check /path/to/commit-message.txt
mise exec -- prek run commit-check --hook-stage commit-msg --commit-msg-filename /path/to/commit-message.txt
```

Empty messages pass so Git can abort normally. `Merge ` subjects are permitted;
reverts use `revert: ...`. Git `Revert "..."`, `fixup!`, `squash!`, and `amend!`
subjects are rejected. Scoped subjects and breaking-change notation are
supported. Commitizen checks syntax; maintainer review checks meaning.

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
simulator environment, pinned Go dependencies, and dprint plugin, validates the
prek configuration, and runs `mise run check` and `mise run test` separately.
The test task covers simulator/gateway unit tests and the Docker integration
checks described above.
The result is informational for merging; requiring the status check is deferred until the
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
with the race detector, and an explicit broker integration task. `gateway:check`
runs source checks without tests. Root common verbs include gateway checks;
root `test` includes the unit tests and Docker integration
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
