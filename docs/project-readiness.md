# Pre-Implementation Readiness

- **Status:** In review
- **Scope:** Before Phase 01 runtime implementation

This document owns the cross-cutting readiness gate and its evidence. It does not redefine product scope, requirements, contracts, architecture, agent rules, or implementation tasks; each check links to the document that owns that information.

## Readiness gate

Phase 01 should not begin until each area is accepted or its remaining uncertainty has an owner and a documented follow-up.

| Area | Owner | Gate condition |
|---|---|---|
| Product intent and boundary | [Vision](product/vision.md), [Scope](product/scope.md) | Purpose, version 0.1 boundary, non-goals, and completion criteria are accepted. |
| Requirements and domain | [Requirements](product/requirements.md), [Domain model](product/domain-model.md), [Workflows](product/workflows.md) | Core entities, requirement identifiers, and telemetry-to-maintenance journeys are understood. |
| Producer contract | [Telemetry contract](specs/telemetry-contract.md) | The active contract is accepted, or every open question has an owner, ADR, experiment, or explicit decision. |
| System design | [Architecture overview](architecture/overview.md), [Data flow](architecture/data-flow.md), [Runtime boundaries](architecture/runtime-boundaries.md) | Responsibilities, data stages, storage roles, and local deployment direction are clear. |
| Implementation plan | [Task index](tasks/README.md), relevant specification, and Week 01 journal (to be created) | The next phase has an implementation-ready specification, tasks, evidence expectations, and journal plan. |
| Tooling and validation | [Phase 00 tasks](tasks/phase-00-foundation.md) and project setup | Supported toolchains and repeatable format, lint, test, and integration commands are selected or explicitly tracked. |
| Governance and data hygiene | Project governance files and this checklist | License, contribution expectations, provenance, reproducibility, and public-repository safeguards are recorded. |
| Agent collaboration | [AGENTS.md](../AGENTS.md), [working agreement](working-agreement.md) | Agent boundaries, review expectations, and evidence rules are aligned with the repository. |

The Week 01 journal is a placeholder until the Phase 01 weekly entry is created. The gate may record a deliberate follow-up instead of blocking on a decision that is not needed for the next implementation slice.

## Review expectations

### Product and domain

- [ ] Review the [product vision](product/vision.md), [scope](product/scope.md), [requirements](product/requirements.md), [domain model](product/domain-model.md), and [workflows](product/workflows.md) together.
- [ ] Confirm that synthetic conditions, health scores, and anomaly observations are described with their limitations.
- [ ] Keep future asset types, advanced models, hardware, and optional assistants outside version 0.1 unless the scope owner changes it.

### Contracts and architecture

- [ ] Review the [telemetry contract](specs/telemetry-contract.md) and resolve or assign its open questions.
- [ ] Create the next capability specification before its implementation phase rather than extending the producer contract with unrelated behavior.
- [ ] Confirm that the [architecture](architecture/overview.md) and [runtime boundaries](architecture/runtime-boundaries.md) do not imply unnecessary process boundaries.

### Governance and tooling

- [ ] Select and document the repository license.
- [ ] Record contribution, conduct, security, issue, and pull-request follow-ups.
- [ ] Select supported Go, Python, Node.js, and package-manager versions plus formatter, linter, type-checker, and test-runner expectations.
- [ ] Establish a clean-checkout validation path and ensure CI will run the same focused checks once runtime code exists.

### Quality, data, and analytical claims

- [ ] Define the project-wide definition of done and the division between unit, contract, integration, end-to-end, and load evidence.
- [ ] Record simulator configuration, seed, generator version, source revision, and dataset/model provenance for analytical work.
- [ ] Keep simulator ground truth separate from inference inputs and document what synthetic experiments cannot prove about physical equipment.
- [ ] Establish observability, failure-recovery, replay, and benchmark evidence before making performance or reliability claims.

### Physical edge preparation

- [ ] Keep the producer contract independent of simulator internals.
- [ ] Define clock quality, sequence gaps, buffering, reconnect, calibration, and orientation assumptions in the edge-integration work before hardware is connected.
- [ ] Plan a compatibility test showing that a physical producer can replace the simulator without downstream special cases.

## Decisions intentionally deferred

These do not block the documentation foundation, but they must be resolved before the relevant implementation phase:

- final open-source license;
- exact toolchain versions and CI provider;
- MQTT QoS and session settings;
- internal event encoding and topic policy;
- production authentication and authorization;
- physical sensor and edge platform;
- cloud deployment topology; and
- optional document retrieval or maintenance-assistant features.

## Exit record

When the gate is reviewed, update the [Week 00 journal](journal/week-00-foundation.md) with:

- the review date;
- decisions accepted;
- questions assigned to ADRs or experiments;
- items intentionally deferred; and
- the owner or process responsible for the next review.
