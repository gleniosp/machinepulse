# EXP-0002 — Synthetic condition separation

- **Status:** Planned
- **Date started:**
- **Date completed:**
- **Owner:** Phase 01 implementation
- **Related requirements:** FR-003, FR-005, FR-017, NFR-009
- **Related specifications:** [Simulator behavior](../specs/simulator.md)
- **Related ADRs:**
- **Code revision:**
- **Dataset or generator version:**

## Question

Are the three synthetic conditions distinguishable enough in exploratory signal
and spectral views to exercise downstream processing and explain limitations?

## Hypothesis

Condition-specific components will create visible differences in selected
time-domain and frequency-domain summaries under controlled changes in
condition intensity.

## Setup

Generate balanced, fixed-seed datasets for normal, imbalance, and overheating.
Inspect plots and simple feature summaries while keeping ground-truth labels
outside the production telemetry input.

## Variables

### Controlled variables

- Sampling, window duration, nominal RPM, seed policy, and generator version.

### Independent variables

- Operating condition and condition intensity.

### Measured variables

- Feature distributions, spectral peaks, temperature/RPM context, and plot
  interpretability.

## Reproduction command

```text
# Add the exact command once the simulator CLI exists.
```

## Results

Record plots, summaries, and cases where conditions overlap.

## Interpretation

Use the results to refine parameter defaults and document what the simulator can
and cannot demonstrate.

## Limitations

Separability in synthetic data does not establish physical diagnosability or
model performance on real equipment.

## Decision or next action

Update the simulator specification, Week 01 article evidence, and any later
feature/evaluation experiments.
