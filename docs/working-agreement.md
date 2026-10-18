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
- reading and respecting the relevant repository specifications and GitHub issues;
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
4. Draft specifications and proposals.
5. Journal notes and experiments as evidence of what has happened.
6. Existing implementation behavior, which may reveal drift or an undocumented decision.

If the conflict materially affects scope, architecture, data semantics, or safety claims, stop and surface it. Do not resolve it through a hidden assumption.

## Git and repository hygiene

- Each week's work uses one dedicated branch and one pull request. When a week maps directly to a phase, the phase branch and pull request are the same unit of work. Suggest branch names in `phase-XX/task-description` form for phase work, combining the phase name with a short description of the first task in that phase (for example, `phase-01/vibration-generation`), and `week-XX/short-description` form for other weekly work. For work outside the numbered phases, the maintainer may approve separate task-oriented branches and pull requests. The approved public-onboarding sequence is `chore/github-planning`, followed after merge by `feat/public-onboarding`, both targeting `main`; its scope is tracked in the [public-onboarding milestone](https://github.com/gleniosp/machinepulse/milestone/10). The maintainer creates or switches to the branch.
- The agent does not create branches or commits. Within the weekly or phase branch, each coherent completed task or step should be represented by a commit. The agent proposes commit boundaries and commands; the maintainer decides the commit packages and executes them.
- Record implementation completion through checked acceptance criteria and evidence on the GitHub issue before raising its pull request. Do not maintain a second live task status in repository documents. The maintainer owns pull-request creation, review, approval, and merging. Keep related GitHub issues open until the pull request containing their changes has merged; close them only after that merge and when their acceptance criteria and evidence are complete.
- Do not reset, revert, delete, or overwrite work unless the maintainer explicitly requests the operation and its target is clear.
- When a commit is requested, use a Conventional Commit / Commitizen-compatible message with a lowercase imperative subject and a short explanation of why the change exists.
- Keep secrets, private information, proprietary data, and unlicensed external material out of the repository. Record provenance and licensing for external datasets, models, documents, images, and code.
- GitHub is the operational source of issue and milestone state. If it is unavailable, record the blocker and do not invent completion state.

## When the maintainer asks to move to the next task

The agent should perform the following sequence without requiring the maintainer to provide a guessed issue number:

1. Inspect GitHub milestones and open issues for `gleniosp/machinepulse`.
2. Select the earliest active milestone with unfinished work, unless the maintainer names another milestone.
3. Select the first open, unblocked issue in that milestone, prioritizing high-priority work and then the stable task ID where one exists.
4. Read the issue, its milestone, linked specification, relevant journal entry, and applicable ADRs or experiments.
5. Check whether the issue is implementation-ready.
6. If context is missing, create or update the required specification, issue acceptance criteria, milestone description, or experiment before coding.
7. Propose the weekly, phase, or approved task-oriented branch name and wait for the maintainer to create or select the branch.
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
    → linked specification and issue acceptance criteria
    → task implementation
    → tests or other evidence
    → journal entry
    → ADR or experiment when needed
    → issue acceptance criteria checked with evidence
    → maintainer raises, reviews, and merges the pull request
    → related GitHub issue closed
```

A new document is warranted when it answers a question that would otherwise be repeated, records a decision with lasting consequences, defines behavior needed by implementation, or preserves evidence needed to evaluate the result.

### Documentation ownership

Keep one authoritative location for each fact. Use the [documentation hub](README.md) to identify the owner, update that owner when the fact changes, and link to it from context documents. Do not paste product definitions into tasks, technical contracts into journals, or progress notes into specifications.

### Acceptance criteria and progress

GitHub issues own live task scope, acceptance checklists, dependencies,
assignment, and progress. Milestones group the issues and track phase delivery.
Write each acceptance criterion as a separate, verifiable Markdown checkbox
(`- [ ]`) on its issue. Check it only when linked evidence demonstrates that
it is satisfied. An implementation can be complete while its issue stays open
for review and merge; record that distinction on the issue rather than in a
second repository status field.

Repository requirements, specifications, and ADRs own product and technical
behavior. Journals and experiments own factual evidence. The concise
[roadmap](roadmap.md) links to GitHub without maintaining phase pages, task
lists, or historical planning archives. Keep stable task IDs on their issues
and in evidence references. Before retiring an existing repository task record,
compare it with its GitHub issue and transfer any missing scope, acceptance
criteria, dependencies, and evidence links. Apply the same organization to
completed and upcoming tasks. Preserve historical evidence in journals,
experiments, ADRs, and Git history rather than keeping a second task archive
beside the live issues.

Use the [issue](templates/github-issue.md) and
[milestone](templates/github-milestone.md) templates when useful. Keep issue
acceptance criteria on issues and phase exit criteria in milestone descriptions.
Select next work by inspecting GitHub, not by inferring priorities from journal
entries, roadmap prose, or other repository documents.

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
- close a related issue only after its pull request has merged and its
  acceptance criteria and evidence are complete.

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

A task's implementation is complete when:

- every acceptance criterion has supporting evidence and is checked on the GitHub issue;
- relevant tests, measurements, screenshots, plots, or other evidence are available;
- affected specifications and GitHub planning are current;
- the journal records what happened and any limitations;
- required ADRs or experiments are linked.

Record these conditions on the GitHub issue as soon as they are met. Do not
require a separate repository task-status update.

The related GitHub issue remains open while its pull request is pending. After
the maintainer-approved weekly or phase pull request is merged, close the issue
if its acceptance criteria and evidence are complete.

Record phase exit evidence in the repository and link it from the milestone
or its issues. Track phase delivery through the GitHub milestone rather than
updating a second live phase status in the repository. Journal summaries may
describe what was demonstrated without mirroring issue or pull-request state.

A GitHub milestone is complete only when all mapped issues are closed, its exit
evidence is recorded, and no scope change is being hidden as completion.

Every handoff should summarize:

- GitHub issue completed or still in progress;
- files and behavior changed;
- validation commands and results;
- documentation, ADR, or experiment updates;
- unresolved questions or risks; and
- the next available issue.
