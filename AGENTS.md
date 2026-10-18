# Agent instructions

MachinePulse is an open-source, simulation-first condition-monitoring platform for rotating machinery. Runtime implementation is underway; use the documentation hub for technical context and GitHub milestones for delivery progress.

## Read before changing

Use the [documentation hub](docs/README.md) to find the owner of the information you need. Read the smallest relevant set of documents:

- [Product scope](docs/product/scope.md) owns version 0.1 boundaries and non-goals.
- [Product requirements](docs/product/requirements.md) owns requirement identifiers.
- [Specifications](docs/specs/README.md) own expected capability behavior and contracts.
- [Roadmap](docs/roadmap.md) points to GitHub milestones and issues, which own implementation scope, acceptance checklists, dependencies, priorities, and progress.
- [Engineering journal](docs/journal/README.md) owns factual progress and discoveries.
- [Working agreement](docs/working-agreement.md) owns maintainer-agent collaboration and GitHub workflow.

Do not copy information between these sources. Update the document that owns a fact and link to it from other documents when context is needed. Draft material is a proposal, not an accepted decision; follow the source-of-truth order in the working agreement.

## Project boundaries

- Keep version 0.1 within the [product scope](docs/product/scope.md).
- Keep the simulator interchangeable with a later physical producer through the [telemetry contract](docs/specs/telemetry-contract.md).
- Treat synthetic signals, health scores, and anomaly results as engineering evidence, not validated or safety-critical diagnoses.
- Follow the responsibility boundaries in the [architecture documentation](docs/architecture/overview.md).
- Do not add hidden external services, proprietary data, secrets, or optional features that displace the core telemetry-to-maintenance path.

Task-specific agent skills, when needed, belong under `.agents/skills/` and should be loaded only for the task they cover.
