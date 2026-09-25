# Working Agreement

**Status:** Proposed for review

This document describes how the project maintainer and AI agents work together on MachinePulse. It complements the technical instructions in the root [`AGENTS.md`](../AGENTS.md).

## Roles

### Project maintainer

The project maintainer owns:

- product direction and scope;
- final decisions on unresolved technical or domain questions;
- review of code, documentation, experiments, and generated data;
- changes in priorities or development sequence; and
- approval of significant changes that affect cost, external services, hardware, licensing, or public project policy.

The maintainer may ask the agent to plan, discuss, investigate, implement, revise, or move to the next task. The latest explicit maintainer direction takes precedence over an older draft plan.

### Repository guardian and implementation agent

The agent is responsible for keeping the repository coherent while implementing requested work. This includes:

- discovering the next actionable GitHub issue;
- reading and respecting the relevant local specifications and task documents;
- creating or updating specifications when the implementation requires them;
- creating ADRs for durable decisions;
- creating experiments for uncertain questions;
- maintaining factual engineering-journal evidence;
- implementing code and tests within the agreed scope;
- updating GitHub issue state through the authenticated `gh` CLI; and
- reporting completed work, validation, decisions, limitations, and the next available task.

The agent may create new documentation when it is required to keep the specification-to-implementation path complete. It must not silently change product scope or accept a materially different architecture merely to make an implementation convenient.

### Additional agents

When sub-agents are used, the repository guardian assigns disjoint file scopes and remains responsible for reviewing the combined result. Important decisions and evidence must be recorded in the repository rather than existing only in an agent conversation.

## Source-of-truth order

Use the following order when information conflicts:

1. The latest explicit instruction from the project maintainer.
2. Accepted product specifications and accepted ADRs.
3. The active GitHub issue and milestone acceptance criteria.
4. Draft specifications and planned task documents.
5. Journal notes and experiments as evidence of what has happened.
6. Existing implementation behavior, which may reveal drift or an undocumented decision.

If the conflict materially affects scope, architecture, data semantics, or safety claims, stop and surface it. Do not resolve it through a hidden assumption.

## Git and repository hygiene

- Each week's work uses one dedicated branch and one pull request. When a week maps directly to a phase, the phase branch and pull request are the same unit of work. The agent proposes a clear task-oriented branch name; the maintainer creates or switches to the branch.
- The agent does not create branches or commits. Within the weekly or phase branch, each coherent completed task or step should be represented by a commit. The agent proposes commit boundaries and commands; the maintainer decides the commit packages and executes them.
- The maintainer owns pull-request creation, review, approval, and merging. Keep related GitHub issues open until the pull request containing their changes has been merged; only then may the issue be closed when its acceptance criteria and evidence are complete.
- Do not reset, revert, delete, or overwrite work unless the maintainer explicitly requests the operation and its target is clear.
- When a commit is requested, use a Conventional Commit / Commitizen-compatible message with a lowercase imperative subject and a short explanation of why the change exists.
- Keep secrets, private information, proprietary data, and unlicensed external material out of the repository. Record provenance and licensing for external datasets, models, documents, images, and code.
- GitHub is the operational source of issue and milestone state. If it is unavailable, record the blocker and do not invent completion state.

## When the maintainer asks to move to the next task

The agent should perform the following sequence without requiring the maintainer to provide a guessed issue number:

1. Inspect GitHub milestones and open issues for `gleniosp/machinepulse`.
2. Select the earliest active milestone with unfinished work, unless the maintainer names another milestone.
3. Select the first open, unblocked issue in that milestone, prioritizing high-priority work and then the local task ID.
4. Read the issue, linked specification, related phase task, relevant journal entry, and applicable ADRs or experiments.
5. Check whether the issue is implementation-ready.
6. If context is missing, create or update the required specification, task breakdown, or experiment before coding.
7. Propose the weekly or phase branch name and wait for the maintainer to create or select the branch.
8. Implement the smallest complete slice that satisfies the issue.
9. Run the narrowest relevant validation first, then broader checks when available.
10. Record evidence in the journal and update any affected specification, ADR, or experiment.
11. Report the proposed commit boundary and pull-request handoff. Leave the issue open until the maintainer-approved pull request is merged; the maintainer closes it only when all acceptance criteria and evidence are satisfied.

Example discovery command:

```bash
gh issue list \
  --repo gleniosp/machinepulse \
  --state open \
  --milestone "Phase 00 — Foundation and readiness" \
  --limit 100
```

If every issue in the active milestone is blocked, the agent should explain the blockers and propose the smallest decision or experiment needed to continue.

## Documentation-to-code workflow

For each meaningful slice:

```text
GitHub issue
    → specification and acceptance criteria
    → task implementation
    → tests or other evidence
    → journal entry
    → ADR or experiment when needed
    → GitHub issue update and closure
```

A new document is warranted when it answers a question that would otherwise be repeated, records a decision with lasting consequences, defines behavior needed by implementation, or preserves evidence needed to evaluate the result.

### Documentation ownership

Keep one authoritative location for each fact. Use the [documentation hub](README.md) to identify the owner, update that owner when the fact changes, and link to it from context documents. Do not paste product definitions into tasks, technical contracts into journals, or progress notes into specifications.

### Acceptance criteria and progress

Write each acceptance criterion as a separate, verifiable Markdown checkbox
(`- [ ]`) in the phase task and its GitHub issue. Leave it unchecked until
evidence shows the criterion is satisfied; then check it in both places and
link the supporting evidence. A task is complete only when every acceptance
criterion is checked and the required evidence is recorded. Keep the GitHub
issue open until its pull request has merged.

## Review and direction changes

After an implementation handoff, the maintainer may:

- review the code and request changes;
- add a discussion or new technical question;
- revise product scope;
- change the implementation sequence;
- reject an approach; or
- ask for a planning-only investigation.

The agent should treat this feedback as the current direction. If the change affects an open or completed issue, the agent should update the issue and relevant local documents rather than continuing from stale assumptions.

When the maintainer asks only for a discussion or plan, do not edit code or documentation until an implementation or documentation change is authorized.

## Agent autonomy and approval boundaries

The agent may perform routine repository work autonomously when it is within an accepted issue:

- inspect files and GitHub state;
- create or update specifications, tasks, journal entries, ADRs, and experiments;
- implement code and tests;
- run documented validation;
- update issue comments, labels, milestones, and issue state through `gh`; and
- close an issue after its evidence is complete.

Ask for maintainer input before:

- changing product scope or version boundaries;
- accepting a materially different architecture or public contract;
- adding paid services, cloud resources, or hidden external dependencies;
- selecting a license or changing repository visibility;
- purchasing or wiring hardware;
- exposing secrets or private data;
- performing destructive operations; or
- closing a milestone when its exit criteria, scope, or evidence are ambiguous.

## Completion and handoff

An issue is complete only when:

- every acceptance criterion has supporting evidence and is checked in the task and GitHub issue;
- relevant tests, measurements, screenshots, plots, or other evidence are available;
- affected specifications and task files are current;
- the journal records what happened and any limitations;
- required ADRs or experiments are linked; and
- the change is merged through the maintainer-approved weekly or phase pull request; and
- the GitHub issue is updated and closed by the maintainer after that merge.

A milestone is complete only when all mapped issues are complete, its exit evidence is recorded, and no scope change is being hidden as completion.

Every handoff should summarize:

- GitHub issue completed or still in progress;
- files and behavior changed;
- validation commands and results;
- documentation, ADR, or experiment updates;
- unresolved questions or risks; and
- the next available issue.
