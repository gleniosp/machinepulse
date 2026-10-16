# MachinePulse Documentation Hub

- **Status:** Phase 02 implementation in progress; P02-001 and P02-002 complete
- **Product version:** 0.1 proposal

This file is the documentation map. It explains where information belongs; it does not restate the product definition, architecture, contracts, task details, or journal evidence maintained by the linked documents.

## Start here

1. Read the [AI-agent instructions](../AGENTS.md) when working as an agent.
2. Read the [working agreement](working-agreement.md) for collaboration, source-of-truth, and delivery rules.
3. Read the [product vision](product/vision.md), [product scope](product/scope.md), and [product requirements](product/requirements.md) for product context.
4. Read the relevant [architecture](architecture/overview.md), [specification](specs/README.md), and [phase task](tasks/README.md) for implementation work.
5. Use the [engineering journal](journal/README.md) for factual progress and evidence.
6. Check [pre-implementation readiness](project-readiness.md) for the phase gates and their evidence.

## Current work

The active milestone is Phase 02: move simulated telemetry through MQTT and the Go gateway into the internal event stream. Its task breakdown is in [Phase 02](tasks/phase-02-telemetry-transport.md), the accepted transport contract is in [Ingestion and Internal Event Boundaries](specs/ingestion.md), and current evidence belongs in [Week 02](journal/week-02-telemetry-ingestion.md). P02-001 and P02-002 are complete; the [local infrastructure guide](../infra/README.md) covers the broker environment. The remaining phase tasks cover gateway implementation and integration. The completed simulator foundation and evidence remain in [Phase 01](tasks/phase-01-simulated-world.md) and [Week 01](journal/week-01-simulated-world.md).

To generate and inspect a local synthetic dataset, start with the [simulator quickstart](guides/simulator-quickstart.md). It links the current file output to the telemetry contract and target architecture without repeating their definitions.

## Document ownership

| Area | Owner | Responsibility |
|---|---|---|
| Product | [Vision](product/vision.md) | Why the product exists, who it serves, and its principles |
| Product | [Scope](product/scope.md) | Version 0.1 inclusion, exclusion, completion, and scope-change rules |
| Product | [Requirements](product/requirements.md) | Stable functional and non-functional requirement identifiers |
| Product | [Domain model](product/domain-model.md) | Canonical entities, relationships, and domain invariants |
| Product | [Workflows](product/workflows.md) | User and system journeys the product should support |
| Product | [Glossary](product/glossary.md) | Shared vocabulary not owned by a single capability |
| Architecture | [Overview](architecture/overview.md) | System shape, storage roles, deployment direction, and evolution |
| Architecture | [Data flow](architecture/data-flow.md) | How data moves, changes meaning, fails, and is replayed |
| Architecture | [Runtime boundaries](architecture/runtime-boundaries.md) | Component ownership and cross-boundary rules |
| Specifications | [Specifications index](specs/README.md) | Specification lifecycle and contract registry |
| Guide | [Simulator quickstart](guides/simulator-quickstart.md) | Simulator purpose, invocation, and interpretation of generated files |
| Guide | [Local telemetry infrastructure](../infra/README.md) | Local broker setup, configuration, readiness, and verification |
| Project operations | [Working agreement](working-agreement.md) | Maintainer-agent collaboration and delivery lifecycle |
| Project operations | [Developer tooling baseline](developer-tooling.md) | Tool, environment, setup, and root task ownership |
| Project operations | [Readiness checklist](project-readiness.md) | Evidence that the project is ready for the next phase |
| Execution | [Task index](tasks/README.md) | Phase map, task conventions, and task status |
| Execution | [Journal index](journal/README.md) | Journal format and evidence rules |
| Decisions | [ADR index](adr/README.md) | Durable architectural decisions and their consequences |
| Investigation | [Experiment index](experiments/README.md) | Reproducible answers to uncertain questions |
| Communication | [Article workflow](blog/README.md) | Evidence-based technical article drafts |

When a fact appears to belong in more than one place, keep the authoritative version in the narrowest owner and add a link from the other document. Do not create a second summary that can drift.

## Documentation lifecycle

The [working agreement](working-agreement.md) owns the project lifecycle. The indexes under `specs/`, `tasks/`, `journal/`, `adr/`, `experiments/`, and `blog/` define the local rules for their document types. Templates are available under [`templates/`](templates/).

## External project state

[GitHub issues](https://github.com/gleniosp/machinepulse/issues) and [milestones](https://github.com/gleniosp/machinepulse/milestones) are the operational source of task state. Repository documents provide the context, acceptance criteria, decisions, and evidence that support that state.
