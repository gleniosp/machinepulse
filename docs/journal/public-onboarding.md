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
