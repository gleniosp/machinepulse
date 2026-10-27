---
name: pull-request
description: Prepare MachinePulse PR content, publish reviewed commits when explicitly requested, or address PR feedback under the maintainer's delivery workflow.
---

# Pull Request

Read [review and publication](../../../docs/working-agreement.md#review-commits-and-publication)
and [progress ownership](../../../docs/working-agreement.md#acceptance-criteria-and-progress).
Use the [PR template](../../../.github/pull_request_template.md) for content;
use [phase-delivery](../phase-delivery/SKILL.md) for local implementation.

- Identify whether the request authorizes content preparation, PR publication,
  committed updates, or local review corrections. Apply the agreement to that
  action; preparation returns text and implementation alone does not publish.
- Before publication, inspect current `origin/main`, the complete branch diff
  and commit series, staged/unstaged/untracked work, issue criteria, and evidence.
  Resolve unreviewed or uncommitted changes with the maintainer. Check for an
  existing branch PR and its base/review state before creating another.
- Describe the final problem and resulting behavior, actual validation,
  evidence/revision, and limits. Reconcile changed scope with the issue; use a
  draft for incomplete work and one closure reference per fully delivered issue.
- On explicit raise-PR authorization, push reviewed commits and create the PR
  against `main`, or reuse its existing PR. With `gh`, use `--body-file` for
  multiline content. Report the PR URL and readiness; maintainer review and
  merge remain the final gate.
- Address feedback locally against the full current change, revalidate affected
  behavior, and update owning evidence and PR content. Follow the same local
  review, maintainer commit, and requested publication sequence for corrections.
