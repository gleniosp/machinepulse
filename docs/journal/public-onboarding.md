# Public Onboarding — Engineering Notes

## 2026-10-18 — Planning ownership

Started [#101](https://github.com/gleniosp/machinepulse/issues/101) in the
[public-onboarding milestone](https://github.com/gleniosp/machinepulse/milestone/10).
The maintainer selected `chore/github-planning` for the first of two PRs.

Updated the [working agreement](../working-agreement.md#acceptance-criteria-and-progress)
and [documentation ownership map](../README.md#external-project-state) to
assign live acceptance checklists and task progress to GitHub. Repository
contracts, decisions, evidence, and completed historical task records retain
their existing roles. The agreement now records the approved off-phase branch
sequence and the requirement to transfer missing issue details before retiring
live repository checklists. Branch, commit, and PR ownership is unchanged.

This first slice changes workflow policy and its ownership map. Task-index and
delivery guidance alignment, the active Phase 02 issue audit, and phase-document
migration remain the next commit-sized slice. No runtime behavior changed.

Validation: `git diff --check` and `mise exec -- prek run --files
docs/working-agreement.md docs/README.md docs/journal/public-onboarding.md`
passed. Applicable file-hygiene hooks passed; runtime checks were skipped by
their file filters. The hook runner needed access to its cache outside the
workspace. No runtime tests were needed for this documentation-only slice.

## 2026-10-18 — Existing task migration

After the workflow-policy commit, the maintainer requested the same cleanup
for completed and upcoming tasks. Audited every detailed repository task
against its GitHub issue before replacing the local records:

| Phase | Task records audited | GitHub owner |
|---|---|---|
| 00 | 10 | [Foundation milestone](https://github.com/gleniosp/machinepulse/milestone/1) |
| 01 | 12 | [Simulator milestone](https://github.com/gleniosp/machinepulse/milestone/2) |
| 02 | 8 | [Transport milestone](https://github.com/gleniosp/machinepulse/milestone/3) |

Retained scope, dependencies, expected evidence, completion boundaries, and
evidence links on the corresponding issues. Made ten historical acceptance
details explicit where the issues did not state them; their checked state
comes from the existing completed repository records, not new runtime tests.
The open Phase 02 acceptance criteria were already present and remain
unchecked. Each migrated issue links to the original task page at the
pre-migration Git revision. Phase exit criteria now live in the three milestone
descriptions; milestone states were not changed.

The maintainer then chose to remove repository phase tracking entirely.
Removed the task directory and phase-task template, replacing them with a
concise roadmap and small GitHub issue and milestone templates. Updated
incoming repository and GitHub links to point to the corresponding issues,
milestones, or evidence. Updated the documentation map, root agent
instructions, and delivery skill to select next work from GitHub.
Removed the live outcome checklist from Week 02 while preserving its dated
evidence. Journals, experiments, and ADRs retain their factual records; Git
history preserves the former task documents.

Validation:

- Retrieved all 30 updated issue bodies and compared them with the prepared
  migration payloads. Existing issue text, checkbox results, and open/closed
  states were preserved.
- Verified the former task pages and phase-task template are removed, with
  no remaining live links to those paths.
- Checked relative Markdown links and anchors in the changed documents.
- File-hygiene hooks passed for the documentation and agent-guidance files;
  runtime hooks were skipped by their file filters. `git diff --check` passed.

Final navigation validation checked 374 local Markdown links and anchors across
the repository. It also found and repaired two older links to the renamed
simulator ground-truth section. The final file-hygiene and Compose configuration
hooks passed. Specification acceptance statements remain normative prose;
implementation checkbox progress belongs to the linked GitHub issues.

The migration changes planning ownership and document navigation only.
Runtime behavior and numbered-phase scope are unchanged. The next delivery
step is maintainer review and commit, followed by the planning PR for #101.

## 2026-10-18 — Container images and local Compose workflow

Started [#104](https://github.com/gleniosp/machinepulse/issues/104) on
`feat/public-onboarding`. Added a root Compose entry point that includes the
existing broker definitions, starts the gateway on the internal MQTT address,
and exposes the simulator as an on-demand tool with host-mounted output.
The [Docker guide](../guides/docker-quickstart.md) owns commands, configuration,
output ownership, readiness interpretation, platform limits, and provenance.

Both image recipes use build and runtime stages with version/digest-pinned
bases. The gateway runs a static Go executable as a non-root user. The
simulator installs the shared Pixi `default` environment during its build and
runs without Pixi or development tools. Its editable source retains the build
path. Dockerfile `COPY` instructions explicitly select dependency manifests,
component source directories, examples, and the license. The context filter
denies files by default and allows only those build inputs. Final exclusions
also remove common local configuration, Git metadata, environments, and caches
inside allowed directories. Unrelated projects and generated datasets remain
outside the build context.
After the maintainer's build-input review, both images rebuilt successfully
with these explicit copies; the simulator generated the three example runs
again and the gateway executable's help command succeeded.
The final context allowlist was also checked by exporting a scratch build's
`COPY . /` result: all 24 exported files were approved manifests, source,
examples, or the license; local configuration, Git data, caches, datasets, and
unrelated directories were absent. The check initially caught parent-directory
exceptions admitting extra project files; the final allowlist omits those
exceptions and uses exact manifest paths and required source subtrees.

The maintainer requested broader host coverage. Added `linux-aarch64` to the
shared Pixi workspace and regenerated the lockfile. The lockfile diff only
adds entries; existing platform selections were preserved. The workspace now
resolves Linux amd64/arm64, macOS Intel/Apple Silicon, and Windows amd64 for
both runtime and development environments. Resolution is not runtime evidence.

Local validation on Linux amd64, Docker Engine 29.7.2 and Compose 5.4.0:

| Check | Evidence |
|---|---|
| `docker compose build gateway simulator` | Both native images built using the locked Go and Pixi inputs |
| `docker compose --project-name machinepulse-container104 run --rm simulator` | Three runs, two windows each; telemetry/sidecar event IDs matched and files belonged to the invoking host user |
| Container manifest inspection | Revision and dirty state were null without build provenance, as documented |
| Runtime image inspection | Simulator runtime had no Pixi, pytest, or checkout metadata; gateway used user `65532:65532` |
| Root Compose startup with disposable project and random host ports | MQTT and Kafka became healthy; gateway logged a successful subscription and connection to `mqtt:1883` |
| Contract fixture published with bundled `mosquitto_pub` | Gateway logged the original event ID and `telemetry_unacknowledged` |
| Gateway restart, then full `down` / `up` preserving volumes | The same pending event was redelivered; the gateway resumed its broker session |
| `docker buildx build --platform linux/arm64 --file infra/docker/gateway.Dockerfile --tag machinepulse-gateway:arm64-check --load .` | Arm64 gateway image cross-built successfully; image architecture was verified |
| `mise run check` | Formatting, lint, typing, 124 simulator tests, Go race tests/build/module verification, expanded lockfile validation, and both Compose configurations passed |
| Repository hooks on all changed and new files | File hygiene, TOML/YAML, simulator, gateway, Compose, and Pixi lock checks passed |
| Documentation navigation and whitespace | 386 local Markdown links/anchors and `git diff --check` passed |

The disposable Compose project's containers, network, and volumes were removed.
Generated sample datasets remain in the ignored host output directory. No
physical telemetry, durable gateway sink, or simulator MQTT publisher was
introduced. The gateway remains in observation mode. Native simulator/gateway
runtime evidence is amd64 only; the host lacks ARM execution support, so the
arm64 simulator and other host platforms have not been runtime-tested here.

This is the first container implementation slice. Repeatable automated
container verification and CI integration remain the next commit-sized step
under #104, before the contribution and public README work.

The maintainer also reported that the manual Docker walkthrough succeeded:
dataset generation, runtime startup, fixture delivery, gateway restart,
container recreation, and shutdown behaved as expected.

## 2026-10-18 — Automated container verification

Added the [container smoke test](../../infra/docker/smoke-test.sh), its
[test-only Compose overrides](../../infra/docker/compose.test.yaml), and a
[runtime evidence checker](../../infra/docker/verify-smoke.py) for #104.
The test builds fresh application layers, runs the simulator twice, compares
the generated files, checks event/sidecar identity and output ownership, and
verifies fixture reception and pending-message recovery after gateway restart
and full container recreation. The evidence checker runs inside the simulator
image with read-only test mounts; it adds no Python requirement on the host or
test files to the runtime image.

The test uses a unique Compose project and image tags, random host ports, and
temporary output. It ignores local dotenv settings and clears inherited tool
profiles; cleanup removes only its own resources. The
[root task](../../mise.toml) exposes `containers:test` and includes it in `test`.
The [PR workflow](../../.github/workflows/pr-checks.yml) invokes it after the
existing broker and gateway integration checks.

Local validation on Linux amd64:

- `mise run containers:test` passed both no-cache builds, byte-for-byte dataset
  comparison, identity/ownership/provenance checks, initial reception, gateway
  restart redelivery, and broker-backed recovery after container recreation.
- The direct Bash command passed with conflicting inherited tool-profile,
  gateway-timeout, and source-revision settings, confirming test isolation.
- Docker inspection after cleanup found no containers, image tags, volumes,
  or networks belonging to either successful test run.
- Bash syntax and Ruff lint/format checks passed for the new test helpers.
- Applicable repository hooks, including YAML/TOML, gateway checks, and Compose
  validation, passed. All 392 local Markdown links/anchors and
  `git diff --check` passed.

The GitHub Actions run awaits the combined public-onboarding PR. Local evidence
covers the current observation-mode workflow and graceful recovery on amd64;
it does not establish native ARM execution, durable Kafka publication, or
power-loss recovery.

## 2026-10-18 — Smoke-test tooling and Docker asset organization

Maintainer review identified that the Python evidence checker had only manual
format checks. Added shared Python 3.13 lint/format settings and static-check tasks
with scoped pre-commit coverage. Root `check`, `format`, `format-check`, and `lint`
include the helper. VS Code selects Ruff for Python and prefers repository
configuration. The helper already passed the selected Ruff formatting rules;
the missing piece was automated coverage and discoverable configuration.

The Bash wrapper and Python module now explicitly document their execution
contexts: Bash orchestrates Docker on the host; the checker runs inside the
simulator's locked Python runtime with read-only fixtures and evidence mounts.
Host-side Ruff checks only parse the file through the pinned Pixi development
toolchain. The [Docker guide](../guides/docker-quickstart.md#repeatable-verification)
and [developer tooling](../developer-tooling.md#container-test-scripts) describe
these roles and commands.

Moved broker Compose configuration and its persistence test into `infra/docker/`,
naming the latter `broker-smoke-test.sh`. Updated the root Compose include,
task commands, Go broker integration harness, documentation, and the owning
GitHub issue's live links. The Mosquitto bind source still resolves to the
existing configuration; Compose project and persistent volume names are
unchanged.

After the move, `mise run test` passed all 124 simulator tests, Go race tests,
broker persistence, gateway MQTT integration, and the no-cache application
container smoke test. `containers:check` and automatic Ruff configuration
discovery also passed. Native runtime evidence remains Linux amd64.
The final pre-commit run explicitly included the new container shell-syntax
hook and passed, alongside JSON/TOML/YAML, gateway, and Compose checks. All
395 local Markdown links/anchors and `git diff --check` passed.

### Shared Python quality policy

Consolidated Ruff and strict mypy settings in root `ruff.toml` and `mypy.ini`,
preserving Python 3.13 and the existing lint rules. Simulator package metadata and pytest
settings stay local. Updated the simulator import roots for the new config
location and added Docker helpers to the mypy targets. Removed the proposed
container-specific Ruff config. Root Python tasks and the shared pre-commit
hook cover all current Python code; focused simulator tasks use the same
policy. Shell syntax checks remain separate, so root checks do not repeat
Python analysis through the container tasks. Smoke-test runtime execution
remains inside Docker.

A tools-only root `pyproject.toml` passed the checks but triggered repeated
missing-project-table warnings from the pinned Pixi version. Dedicated root
config files avoid those warnings without introducing root package metadata.

Validation: `mise run check` passed shared formatting/lint and strict mypy on
23 Python files, all 124 simulator tests, Go checks, lockfile freshness,
Compose validation, and Bash syntax. Focused simulator type checking passed
on 22 files; automatic Ruff discovery also passed for the Docker helper.
Applicable pre-commit hooks, including shared Python coverage, passed. The
lockfile did not change. All 395 local Markdown links and `git diff --check`
passed.

## 2026-10-19 — Provisional contribution guidance

Added [CONTRIBUTING.md](../../CONTRIBUTING.md) for the maintainer-led development
stage, with a discussion-first route for substantial changes. It links to the
existing setup/checks, working agreement, GitHub planning, and artifact
provenance owners. Moved GitHub CLI authentication guidance out of the public
README and made clear that trying the project needs no GitHub authentication.
Updated the tooling guide's incoming link, documentation hub, and governance
follow-up to reflect the provisional guide without claiming broader
contribution readiness. No license, conduct, or disclosure policy was changed.

Validation: applicable pre-commit documentation hooks passed on all six changed
or new Markdown files. All 405 local Markdown links, including anchors, and
`git diff --check` passed. Checked the authentication text against the pinned
`gh auth login --help` and official CLI documentation. This slice changes only
documentation; runtime tests were not repeated.

### Guided public issue forms

Added GitHub issue forms for bug reports and feature/improvement proposals,
plus a chooser link to the provisional contribution guide. Bug reports ask
for expected/actual behavior, reproduction, and optional environment/evidence;
proposals start with the problem and invite discussion before substantial
implementation. At maintainer request, blank issues are disabled for public
intake so reports use these forms. No labels, assignees, or
milestones are assigned automatically. These public intake forms complement
the existing maintainer issue/milestone drafting guides rather than replacing
GitHub as the owner of implementation scope and progress.

Validation: YAML and applicable documentation hooks passed for the three new
chooser/form files and affected guides. All 406 local Markdown links/anchors
and `git diff --check` passed. Reviewed the form fields and chooser configuration
against GitHub's documented syntax. GitHub's live issue chooser will become
available after these files merge into the default branch; no live form
submission was made during local validation.

## 2026-10-19 — Public README refresh

Reworked the README into a concise introduction to condition monitoring and the
simulation-first approach, with a development warning, current capabilities,
intended architecture, Docker quickstart, and reliability boundaries. Linked
technical owners and GitHub implementation tracking instead of copying their
checklists. The overview explicitly distinguishes file generation and gateway
observation mode from planned publication, storage, analytics, and maintenance
workflows. At-least-once delivery, stable identity, separate event/receipt time,
and tested session recovery are distinguished from future deduplication,
quarantine, consumer retries, replay, and producer buffering.

Executed the displayed Docker commands on Linux amd64. The simulator image
rebuilt from the current package configuration and generated the three example
runs (two windows each), with the expected JSONL and manifest files owned by
the host account. Runtime startup rebuilt the gateway image, started the two
brokers and gateway, and produced `mqtt_connected` logs. The gateway resumed an
existing persisted session and redelivered its pending fixture, so it correctly
did not emit `mqtt_subscribed`; the README log hint now distinguishes a new
session. `docker compose down` removed the containers/network while retaining
broker volumes and generated data. No existing dataset or broker volume was
removed. Native evidence remains Linux amd64.

`mise run hooks:check` passed across the repository, including simulator tests,
shared Python checks, Go checks, Compose validation, shell syntax, and lockfile
freshness. The README is approximately 550 words. Local Markdown links and
`git diff --check` passed. GitHub Actions and live issue-form behavior still
await the pull request and merge respectively.
