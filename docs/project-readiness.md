# Pre-Implementation Readiness

- **Status:** Accepted for Phase 01; later-phase follow-ups tracked
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
| Tooling and validation | [Developer tooling baseline](developer-tooling.md), [Phase 00 tasks](tasks/phase-00-foundation.md) | Supported toolchains and repeatable format, lint, test, and integration commands are selected or explicitly tracked. |
| Governance and data hygiene | Project governance files and this checklist | License, contribution expectations, provenance, reproducibility, and public-repository safeguards are recorded. |
| Agent collaboration | [AGENTS.md](../AGENTS.md), [working agreement](working-agreement.md) | Agent boundaries, review expectations, and evidence rules are aligned with the repository. |

The Week 01 journal is a placeholder until the Phase 01 weekly entry is created. The gate may record a deliberate follow-up instead of blocking on a decision that is not needed for the next implementation slice.

## Staged gate policy

This is a phase-scoped gate, not a requirement that every future concern be
resolved before the first runtime code exists. Before a phase starts, every
readiness item needed by that phase must be accepted or have an explicit owner
and follow-up. Phase-specific executable evidence may be completed during the
phase before its exit review. Concerns owned by later phases remain deferred and
are not blockers for earlier work.

## Required before Phase 01 implementation

### Product and domain

- [x] Review the [product vision](product/vision.md), [scope](product/scope.md), [requirements](product/requirements.md), [domain model](product/domain-model.md), and [workflows](product/workflows.md) together.
- [x] Confirm that synthetic conditions, health scores, and anomaly observations are described with their limitations.
- [x] Keep future asset types, advanced models, hardware, and optional assistants outside version 0.1 unless the scope owner changes it.

### Contracts and architecture

- [x] Review the [telemetry contract](specs/telemetry-contract.md) and resolve or assign its open questions.
- [x] Create the next capability specification before its implementation phase rather than extending the producer contract with unrelated behavior.
- [x] Confirm that the [architecture](architecture/overview.md) and [runtime boundaries](architecture/runtime-boundaries.md) do not imply unnecessary process boundaries.

### Governance and tooling

- [x] Select and document the repository license.
- [x] Record contribution, conduct, security, issue, and pull-request follow-ups.
- [x] Select supported Go, Python, Node.js, and package-manager versions plus formatter, linter, type-checker, and test-runner expectations.
- [x] Define the project-wide definition of done and the division between unit, contract, integration, end-to-end, and load evidence through the [working agreement](working-agreement.md), [task conventions](tasks/README.md), and [developer tooling baseline](developer-tooling.md).

## Required during Phase 01 before phase exit

- [ ] Establish a clean-checkout validation path and ensure CI will run the same focused checks once runtime code exists. This is owned by P01-008.
- [x] Record simulator configuration, seed, generator version, source revision, and dataset/model provenance for analytical work.
- [x] Keep simulator ground truth separate from inference inputs and document what synthetic experiments cannot prove about physical equipment.

## Deferred to later phases

- Establish observability, failure-recovery, replay, and benchmark evidence in
  the reliability phase before making performance or reliability claims.
- Define clock quality, sequence gaps, buffering, reconnect, calibration, and
  orientation assumptions in the physical edge phase before hardware is
  connected.
- Plan a compatibility test showing that a physical producer can replace the
  simulator without downstream special cases in the physical edge phase.
- Keep the producer contract independent of simulator internals; this is already
  accepted as a standing architectural constraint.

## Decisions intentionally deferred

These do not block the documentation foundation, but they must be resolved before the relevant implementation phase:

- final contribution, conduct, security, and artifact-review policies;
- exact toolchain versions and CI provider;
- MQTT QoS and session settings;
- internal event encoding and topic policy;
- production authentication and authorization;
- physical sensor and edge platform;
- cloud deployment topology; and
- optional document retrieval or maintenance-assistant features.

## Review record — 2026-09-19

The readiness checklist and its linked source documents were reviewed. Product
intent and boundary, requirements and domain, producer-contract follow-ups,
system design, the Phase 01 implementation plan, governance baseline, and agent
collaboration are documented sufficiently for planning.

The P00-010 tooling baseline is accepted. Exact patch versions, CI provider,
and clean-checkout execution remain assigned to the implementation setup and
P01-008 validation work. Phase 01 runtime implementation may begin under the
accepted baseline, but Phase 01 is not complete until its executable validation
commands have been run and recorded.

## Exit record

When the gate is reviewed, update the [Week 00 journal](journal/week-00-foundation.md) with:

- the review date;
- decisions accepted;
- questions assigned to ADRs or experiments;
- items intentionally deferred; and
- the owner or process responsible for the next review.
