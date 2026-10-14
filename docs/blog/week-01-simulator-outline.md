# From Machines to Data: Modeling Industrial Sensor Telemetry Without Hardware

- **Status:** Source outline for the [evidence-based article draft](week-01-simulator.md)
- **Related journal:** [Week 01](../journal/week-01-simulated-world.md)
- **Related specification:** [Simulator behavior](../specs/simulator.md)

## Technical question

How can a software-only simulator create useful engineering evidence for a
condition-monitoring pipeline without pretending to reproduce a real motor?

## Outline

1. **The problem:** raw sensor data needs context, windows, units, and traceable
   run metadata before downstream systems can use it.
2. **The contract boundary:** explain why simulator output follows the same
   producer-facing telemetry contract intended for future hardware.
3. **The simulated motor:** describe nominal RPM, three-axis vibration,
   temperature, and operating-condition configuration.
4. **Reproducibility:** show how seed, configuration, generator version, and
   code revision make a run repeatable.
5. **Separating truth from telemetry:** explain why condition labels live in a
   sidecar and are not inference features.
6. **Evidence:** include time-domain plots, spectra, contract-test output, and a
   repeatability comparison.
7. **Limitations:** distinguish synthetic engineering behavior from validated
   fault physics and safety-critical diagnosis.
8. **What comes next:** connect the simulator to MQTT without changing the
   downstream producer contract.

## Evidence checklist

- [x] Reproducible command and configuration manifest.
- [x] Normal, imbalance, and overheating plots.
- [x] Contract validation output and invalid fixtures.
- [x] Ground-truth sidecar example.
- [x] Experiment results and limitations.
