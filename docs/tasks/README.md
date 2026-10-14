# Implementation Tasks

Tasks translate accepted product requirements and technical specifications into executable work. This index owns the phase map, task format, and task statuses; the [working agreement](../working-agreement.md) owns how tasks are selected, implemented, reviewed, and synchronized with GitHub.

## Task hierarchy

```text
product requirement
    → technical specification
    → phase task
    → implementation and test
    → journal evidence
```

A task should not introduce behavior absent from the relevant specification unless the specification is updated in the same change.

## Phase map

| Phase | Focus | Journal |
|---|---|---|
| 00 | Documentation foundation and project setup | [Week 00](../journal/week-00-foundation.md) |
| 01 | Simulated industrial world and polyglot workspace foundation | Week 01 |
| 02 | Telemetry transport and ingestion | Week 02 |
| 03 | Storage and data quality | Week 03 |
| 04 | Signal processing | Week 04 |
| 05 | Anomaly detection and health scoring | Week 05 |
| 06 | Maintenance product and dashboard | Week 06 |
| 07 | Reliability and observability | Week 07 |
| 08 | Physical edge integration | Week 08 |

Phases 00 and 01 are currently drafted in detail. Create or refine later task files immediately before their implementation phase.

## Task conventions

Each task should have:

- a stable identifier preserved in its GitHub issue title;
- a local status that reflects task and evidence completion;
- a clear outcome;
- links to requirements and specifications;
- acceptance criteria written as separate, verifiable Markdown checkboxes;
- tests or evidence expected;
- dependencies;
- an explicit out-of-scope section; and
- a definition of done.

Leave acceptance checkboxes unchecked until their evidence satisfies the
criterion. Check each item when it is complete; a task is complete when all of
its criteria are checked and the required evidence is recorded. Set its local
status to **Complete** as soon as those conditions are met, before opening the
pull request. Local completion does not wait for the pull request to merge;
GitHub issue closure follows the merged pull request under the
[working agreement](../working-agreement.md).

Suggested identifiers are `P00-001`, `P01-001`, and so on. A journal entry should reference these identifiers rather than copy the task text.

## Statuses

- **Planned** — identified but not ready to implement.
- **Ready** — specification and dependencies are clear.
- **In progress** — actively being implemented.
- **In review** — phase-level plan or evidence is awaiting maintainer review;
  finished local tasks remain **Complete**.
- **Blocked** — requires a decision, experiment, or external input.
- **Complete** — acceptance criteria and evidence are satisfied.
- **Deferred** — intentionally moved out of the current scope.

Task-level and phase-level statuses track local work. Mark a phase **Complete**
when its local definition of done is satisfied, even if its pull request has not
merged. Track pull-request and issue state in GitHub; do not change a local task
or phase status after merge only to record that delivery state.

## Open-source task hygiene

Tasks and examples must not include credentials, proprietary data, or references to local filesystem paths. Dataset-related tasks must identify data provenance and licensing requirements.
