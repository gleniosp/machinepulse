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
| 01 | Simulated industrial world | Week 01 |
| 02 | Telemetry transport and ingestion | Week 02 |
| 03 | Storage and data quality | Week 03 |
| 04 | Signal processing | Week 04 |
| 05 | Anomaly detection and health scoring | Week 05 |
| 06 | Maintenance product and dashboard | Week 06 |
| 07 | Reliability and observability | Week 07 |
| 08 | Physical edge integration | Week 08 |

Only Phase 00 is currently drafted in detail. Create or refine later task files immediately before their implementation phase.

## Task conventions

Each task should have:

- a stable identifier preserved in its GitHub issue title;
- a clear outcome;
- links to requirements and specifications;
- acceptance criteria;
- tests or evidence expected;
- dependencies;
- an explicit out-of-scope section; and
- a definition of done.

Suggested identifiers are `P00-001`, `P01-001`, and so on. A journal entry should reference these identifiers rather than copy the task text.

## Statuses

- **Planned** — identified but not ready to implement.
- **Ready** — specification and dependencies are clear.
- **In progress** — actively being implemented.
- **Blocked** — requires a decision, experiment, or external input.
- **Complete** — acceptance criteria and evidence are satisfied.
- **Deferred** — intentionally moved out of the current scope.

## Open-source task hygiene

Tasks and examples must not include credentials, proprietary data, or references to local filesystem paths. Dataset-related tasks must identify data provenance and licensing requirements.
