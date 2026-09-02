# Product Workflows

- **Status:** Draft
- **Version:** 0.1

These workflows describe the user and system journeys MachinePulse should support. They own sequencing and outcomes, not field definitions, component ownership, or retry mechanics. See the [telemetry contract](../specs/telemetry-contract.md) for producer data, [runtime boundaries](../architecture/runtime-boundaries.md) for component responsibility, and [data flow](../architecture/data-flow.md) for processing semantics.

## 1. Register an asset and producer

1. Create an asset representing a motor.
2. Register a simulator or edge producer.
3. Associate the producer with the asset.
4. Configure the asset and producer for the intended operating regime.
5. Mark the producer as ready to publish telemetry.

The simulator should perform this setup through a reproducible command or fixture.

## 2. Produce telemetry

1. The producer samples or generates measurements.
2. It groups them into a contract-compliant telemetry window.
3. It publishes the window through the device-facing transport boundary.
4. If delivery is retried, the producer preserves the event identity.

A physical producer must follow the same [producer-facing contract](../specs/telemetry-contract.md).

## 3. Ingest and validate telemetry

1. The gateway receives a device message.
2. It validates the message against the active contract.
3. It records the valid or invalid outcome with enough context to investigate it.
4. Valid telemetry enters the internal processing path; invalid telemetry follows the configured quarantine or dead-letter path.

Invalid input must be observable and must not silently disappear.

## 4. Persist and analyze telemetry

1. Source telemetry is retained for traceability.
2. Analytics turns eligible windows into versioned features.
3. A baseline or model produces an anomaly observation with supporting evidence.
4. The source window, analytical method, and result remain linked.

The [data-flow specification](../architecture/data-flow.md) owns the stage transitions and failure behavior.

## 5. Evaluate and present an alert

1. Alert policy receives an anomaly observation.
2. It applies severity, persistence, and asset-context rules.
3. It creates or updates an alert when policy conditions are met.
4. The API exposes the alert and its supporting evidence.
5. The dashboard presents the asset, trend, feature changes, and detection explanation.

The product must distinguish measurements, derived features, model output, policy, and human-entered notes.

## 6. Create and complete a work order

1. An operator reviews an alert.
2. The operator acknowledges it or creates a work order.
3. The work order records the requested action, priority, and status.
4. A technician or operator adds notes and completion information.
5. The alert and work order retain links to the original evidence.

The first version does not automate maintenance execution.

## 7. Replay historical data

1. An operator or developer selects a bounded time range or dataset.
2. The system reprocesses the selected source events.
3. Replay results identify the processing or model version used.
4. Results can be compared without corrupting the original history.

Replay identity, isolation, and idempotency are owned by the [data-flow design](../architecture/data-flow.md) and the ADR or experiment that resolves them.

## 8. Replace the simulator with hardware

1. A physical producer is configured for a device and asset.
2. It publishes the existing producer-facing contract.
3. Downstream consumers process its messages without producer-specific special cases.
4. Timing, noise, dropped messages, and calibration differences are documented as part of the edge-integration work.

This is the primary product test of the simulation-first approach.
