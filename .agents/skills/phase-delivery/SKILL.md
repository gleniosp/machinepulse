---
name: phase-delivery
description: Select a MachinePulse issue or deliver agreed work through implementation, validation, local review, and commit-message handoff.
---

# Phase Delivery

Read the [documentation hub](../../../docs/README.md) and
[working agreement](../../../docs/working-agreement.md) for policy and owning
contracts. This skill routes the request; the agreement owns permissions and
completion rules.

- For next-task requests, follow
  [task selection](../../../docs/working-agreement.md#when-the-maintainer-asks-to-move-to-the-next-task):
  inspect live milestones, priorities, native blockers, related PR/review state,
  and actual prerequisite delivery. Recommend an issue and its branch name;
  identify work awaiting review/merge or unavailable GitHub evidence explicitly.
- For implementation, confirm the agreed issue and actual branch under
  [Git hygiene](../../../docs/working-agreement.md#git-and-repository-hygiene).
  Read the issue, owning specifications, and relevant evidence. Prepare a missing
  contract or experiment before dependent implementation. Preserve unrelated
  work and deliver the complete accepted slice with relevant validation.
- Hand off the working tree, evidence, and limitations for local review and
  acceptance under
  [review and publication](../../../docs/working-agreement.md#review-commits-and-publication).
  Propose coherent commit boundaries; a commit-message request returns text.
  Use the [tooling guide](../../../docs/developer-tooling.md) for format/check
  commands and commit-message validation.
- For PR preparation, publication, or feedback, use the
  [pull-request skill](../pull-request/SKILL.md). Keep issue criteria and
  repository evidence current under
  [progress ownership](../../../docs/working-agreement.md#acceptance-criteria-and-progress).
