# Architecture Decision Records

Architecture Decision Records (ADRs) capture important decisions, alternatives, consequences, and reversals. They explain why the project took a direction; they are not a list of every implementation detail.

## When to write an ADR

Create an ADR when a decision:

- affects a system or runtime boundary;
- introduces a long-lived dependency or operational constraint;
- changes an external or internal contract;
- has meaningful trade-offs;
- is difficult to reverse; or
- would otherwise be repeatedly debated.

Small choices can remain in the relevant specification or task.

## Lifecycle

- **Proposed** — under discussion.
- **Accepted** — the current project decision.
- **Superseded** — replaced by a later ADR.
- **Rejected** — considered and intentionally not selected.

Do not create an accepted ADR for a decision that has not actually been reviewed.

## Naming

Use sequential identifiers and descriptive names:

```text
0001-simulation-first.md
0002-telemetry-event-versioning.md
```

The sequence should not be reused, even if a decision is later rejected or superseded.

## Current status

No formal ADRs have been accepted yet. Candidate decisions are listed in the architecture and telemetry documents and will become ADRs when they are reviewed.

Use the [ADR template](template.md) for new records.
