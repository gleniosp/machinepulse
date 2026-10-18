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
