# Phase 00 — Documentation Foundation

- **Status:** In review
- **Goal:** Establish a coherent product definition, technical direction, and execution system before implementation begins.

## Related documents

- [Project documentation hub](../README.md)
- [Product vision](../product/vision.md)
- [Product scope](../product/scope.md)
- [Domain model](../product/domain-model.md)
- [Product workflows](../product/workflows.md)
- [Product requirements](../product/requirements.md)
- [Architecture overview](../architecture/overview.md)
- [Data flow](../architecture/data-flow.md)
- [Runtime boundaries](../architecture/runtime-boundaries.md)
- [Telemetry contract](../specs/telemetry-contract.md)
- [Pre-implementation readiness](../project-readiness.md)

## Tasks

### P00-001 — Review the project identity

- **Outcome:** The project purpose, principles, intended users, and constraints are accepted.
- **Acceptance criteria:**
  - [x] `vision.md` has been reviewed.
  - [x] The simulation-first and open-source principles are accepted.
  - [x] The experimental and non-safety-critical nature of the system is explicit.
- **Evidence:** Review notes in the Week 00 journal.

### P00-002 — Review version 0.1 scope

- **Outcome:** The first release boundary is clear enough to protect implementation focus.
- **Acceptance criteria:**
  - [x] In-scope capabilities are accepted.
  - [x] Non-goals are accepted.
  - [x] Scope-change rule is accepted.
- **Evidence:** Accepted scope and any deferred items recorded in the journal.

### P00-003 — Review the domain model and workflows

- **Outcome:** The core nouns and user-visible workflows are shared before schemas are implemented.
- **Acceptance criteria:**
  - [x] Asset, device, sensor, telemetry, analytical, and maintenance concepts are understood.
  - [x] The telemetry-to-work-order flow is accepted.
  - [x] Replay and physical-producer workflows have identified open questions.
- **Evidence:** Review notes and amendments to product documentation.

### P00-004 — Review the initial architecture

- **Outcome:** The initial Go, Python, TypeScript, infrastructure, and data-store responsibilities are clear.
- **Acceptance criteria:**
  - [x] Logical boundaries are accepted without requiring one process per component.
  - [x] The simulator and future hardware producer share a contract boundary.
  - [x] PostgreSQL and ClickHouse responsibilities are understood.
  - [x] Local-first execution is the initial deployment goal.
- **Evidence:** Architecture review notes and any accepted ADRs.

### P00-005 — Accept the first telemetry contract

- **Outcome:** The simulator can be implemented against a reviewed contract.
- **Acceptance criteria:**
  - [x] Required fields and units are accepted.
  - [x] Event-time and sequence semantics are accepted.
  - [x] Validation and duplicate expectations are accepted.
  - [x] Simulator ground truth is separated from production telemetry.
  - [x] Open questions have an owner or a follow-up experiment.
- **Evidence:** Contract version updated from Draft to Accepted, or explicit changes recorded.

### P00-006 — Establish documentation workflows

- **Outcome:** Future implementation work has consistent task, journal, ADR, experiment, and blog formats.
- **Acceptance criteria:**
  - [x] Templates are available.
  - [x] Each phase has a clear relationship to its journal week.
  - [x] The blog workflow distinguishes polished articles from raw journal notes.
  - [x] Open-source documentation and data-provenance expectations are visible.
  - [x] Each document type has one owner and cross-references other owners instead of copying their guidance.
- **Evidence:** Links from the documentation hub and journal index.

### P00-007 — Prepare Phase 01

- **Outcome:** The simulator phase is ready to implement without unresolved foundational ambiguity.
- **Acceptance criteria:**
  - [x] Simulator capability specification is drafted.
  - [x] Phase 01 tasks have acceptance criteria.
  - [x] Week 01 journal plan and article outline are ready.
  - [x] Required experiments are identified.
- **Evidence:** Phase 01 task file and Week 01 journal entry.

### P00-008 — Complete the pre-implementation readiness review

- **Outcome:** The project has explicit governance, tooling, quality, data, and agent-readiness expectations before runtime code is added.
- **Acceptance criteria:**
  - [x] The [readiness checklist](../project-readiness.md) has been reviewed.
  - [x] Open-source license and governance follow-ups are recorded.
  - [x] Initial toolchain and validation follow-ups are recorded.
  - [x] Data provenance, reproducibility, and analytical limitations are accepted.
  - [x] `AGENTS.md` is reviewed and linked from the project documentation.
  - [x] Any blocking question has an owner, ADR, experiment, or explicit user decision.
- **Evidence:** Completed checklist sections and Week 00 review notes.

### P00-009 — Select the open-source license and governance baseline

- **Outcome:** The public repository has a clear legal and collaboration baseline.
- **Acceptance criteria:**
  - [x] A project license is selected and documented.
  - [x] Contribution, code-of-conduct, and security-policy follow-ups are defined.
  - [x] Dataset, model, document, and image licensing expectations are recorded.
- **Evidence:** Governance files and a documented license decision.

### P00-010 — Define the developer-tooling and validation baseline

- **Outcome:** Contributors and agents have repeatable commands for the first implementation phase.
- **Acceptance criteria:**
  - [ ] Supported Go, Python, Node.js, and package-manager versions are selected or tracked as open decisions.
  - [ ] Formatter, linter, type-checker, and test-runner choices are recorded.
  - [ ] Initial local and CI command expectations are documented.
  - [ ] Phase 01 includes the commands as executable checks.
- **Evidence:** Developer setup documentation and a clean-checkout validation run.

## Out of scope

- Runtime implementation.
- Selecting the final hardware or sensor.
- Building infrastructure containers.
- Training an anomaly model.
- Publishing a polished blog post before implementation evidence exists.

## Definition of done

Phase 00 is complete when the foundational documents and pre-implementation readiness checklist have been reviewed, the first telemetry contract is accepted or its unresolved decisions are explicitly tracked, and Phase 01 has actionable tasks with testable acceptance criteria.
