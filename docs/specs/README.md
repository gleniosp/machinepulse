# Specifications

Specifications describe expected behavior and constraints for a capability. They are the normative technical references used to create implementation tasks and acceptance criteria. Product documents own intent and scope; architecture documents own system shape; tasks own planned work; and journals own what actually happened.

## Specification lifecycle

```text
Draft → Accepted → In progress → Verified
                  ↓
              Superseded
```

A specification may be updated when implementation or an experiment reveals a better design. Significant changes should link to the relevant ADR or experiment.

## Specification rules

- Describe behavior before implementation details where possible.
- Give important requirements stable identifiers.
- State assumptions and limitations explicitly.
- Define acceptance criteria that can be tested or demonstrated.
- Link related product requirements, tasks, ADRs, and experiments.
- Avoid copying daily progress from the engineering journal.

Specifications should link to the product requirements they satisfy and to architecture, ADRs, experiments, and GitHub issues as needed. They should not become a second product roadmap or an implementation diary.

## Current specifications

| Specification                                           | Status   | Purpose                                                                                                              |
| ------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------- |
| [Telemetry contract](telemetry-contract.md)             | Draft    | Defines the producer-facing telemetry window and initial event semantics                                             |
| [Simulator behavior](simulator.md)                      | Draft    | Defines deterministic motor telemetry generation and ground-truth separation                                         |
| [Ingestion and internal event boundaries](ingestion.md) | Accepted | Defines the MQTT route and delivery boundary into the internal event stream; defers the internal envelope to P02-005 |

The remaining capability specifications will be added just before their implementation phases:

- simulator behavior;
- storage and data quality;
- signal processing;
- anomaly detection;
- maintenance workflows;
- dashboard behavior;
- observability; and
- physical edge integration.
