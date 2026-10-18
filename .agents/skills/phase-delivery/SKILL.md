---
name: phase-delivery
description: Guide MachinePulse work that spans a GitHub issue, phase/week branch, implementation evidence, and pull-request handoff.
---

# Phase Delivery

Use this skill when selecting or implementing a MachinePulse task, preparing a
phase/week delivery, updating its evidence, or handing work to the maintainer
for a pull request. The repository documents remain authoritative; this skill
is an operational route through them, not a replacement for their policy.

## Before changing anything

1. Read [the documentation hub](../../../docs/README.md) and
   [the working agreement](../../../docs/working-agreement.md).
2. Inspect the active GitHub milestone and select the earliest open, unblocked
   issue unless the maintainer names another task. Select priorities from GitHub,
   not repository roadmap prose or historical journal entries.
3. Read the issue, its milestone, the owning specification, the relevant
   journal entry, and any linked ADRs or experiments.
4. Confirm the task is implementation-ready. If a contract, decision, or
   experiment is missing, prepare that prerequisite before coding.

Respect the source-of-truth order in the working agreement. Update the document
that owns a fact instead of copying it into a task or journal.

## Branch and delivery boundaries

- Propose a clear task-oriented branch name and wait for the maintainer to
  create or switch to it. Do not create branches or commits.
- Keep one branch and pull request for the week's work; when the week maps to a
  phase, use the phase as that unit. Follow maintainer-approved task-oriented
  branches and PR boundaries for work outside the numbered phases.
- Keep the implementation focused on the accepted issue and product scope.
- Run the narrowest relevant validation first, then broader checks when they
  exist.
- Record factual results, limitations, and decisions in the journal; link to
  tests, plots, benchmarks, fixtures, ADRs, and experiments.

## Handoff

Before handing off, verify that:

- acceptance criteria, dependencies, and evidence are current on the GitHub issue;
- affected specifications, ADRs, experiments, and journal entries are linked;
- proposed commit boundaries and commands are clear for the maintainer;
- the pull request summary explains scope and validation; and
- related issues remain open until the maintainer-approved pull request merges.

After merge, the maintainer may close the completed issues and milestone. Do
not close them early or use a hidden assumption to bypass an unresolved
decision. Surface scope, architecture, safety, licensing, or external-service
decisions for maintainer approval.
