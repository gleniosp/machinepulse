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
