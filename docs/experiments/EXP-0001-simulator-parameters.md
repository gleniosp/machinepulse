# EXP-0001 — Simulator parameter ranges

- **Status:** Planned
- **Date started:**
- **Date completed:**
- **Owner:** Phase 01 implementation
- **Related requirements:** FR-002, FR-003, FR-004, NFR-001
- **Related specifications:** [Simulator behavior](../specs/simulator.md)
- **Related ADRs:**
- **Code revision:**
- **Dataset or generator version:**

## Question

Which initial window duration, sampling rate, noise level, and condition
parameter ranges produce inspectable synthetic signals without implying physical
validity?

## Hypothesis

A one-second window at 1,600 Hz with bounded, configurable noise will provide a
useful first balance between spectral resolution, local test cost, and readable
plots.

## Setup

Generate fixed-seed windows across normal, imbalance, and overheating settings.
Compare time-domain summaries, spectra, output size, and repeatability.

## Variables

### Controlled variables

- Generator version, seed set, nominal RPM, and asset configuration.

### Independent variables

- Window duration, sample rate, noise level, and condition severity.

### Measured variables

- Generation time, output size, RMS/peak summaries, dominant spectral peaks,
  and qualitative plot readability.

## Reproduction command

```text
# Add the exact command once the simulator CLI exists.
```

## Results

Record measurements and plots after implementation.

## Interpretation

Determine which defaults are suitable for development evidence and which remain
open parameters.

## Limitations

This experiment evaluates engineering usefulness of synthetic signals, not
physical fault-model validity.

## Decision or next action

Update the simulator specification and implementation task defaults.
