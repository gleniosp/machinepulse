# EXP-0001 — Simulator parameter ranges

- **Status:** In progress
- **Date started:** 2026-10-01
- **Date completed:**
- **Owner:** Phase 01 implementation
- **Related requirements:** FR-002, FR-003, FR-004, NFR-001
- **Related specifications:** [Simulator behavior](../specs/simulator.md)
- **Related ADRs:**
- **Code revision:** `ec1bee2e9bb7f4982c62382d259b6b2162b5149d` (working tree contained the P01-004 implementation and experiment script)
- **Dataset or generator version:** `simulator.v1`

## Question

Which initial window duration, sampling rate, noise level, and condition
parameter ranges produce inspectable synthetic signals without implying physical
validity?

## Hypothesis

A one-second window at 1,600 Hz with bounded, configurable noise will provide a
useful first balance between spectral resolution, local test cost, and readable
plots.

## Setup

Generate fixed-seed windows across normal, imbalance, and overheating settings
as their generators are implemented. The P01-004 slice compares normal and
imbalance vibration. Compare time-domain summaries, spectra, output size, and
repeatability.

## Variables

### Controlled variables

- Generator version, seed set, nominal RPM, and asset configuration.

### Independent variables

- Window duration, sample rate, noise level, and condition intensity.

### Measured variables

- Generation time, output size, RMS/peak summaries, dominant spectral peaks,
  and qualitative plot readability.

## Reproduction command

```text
mise run simulator:experiment:vibration
```

## Results

The preliminary P01-004 vibration slice used a one-second window at 1,600 Hz (1,600
samples per axis), 1,800 RPM (30 Hz rotation), seed `1234`, and noise standard
deviation `0.01 m/s²`. The intensity-1.0 imbalance run added its configured
per-axis 30 Hz component. A direct DFT over bins 1–100 Hz found the dominant
component at 30 Hz for every axis and condition:

| Condition | Axis | RMS (m/s²) | Peak (m/s²) | Dominant amplitude at 30 Hz (m/s²) |
|---|---:|---:|---:|---:|
| Normal | X | 0.037095 | 0.073685 | 0.050545 |
| Normal | Y | 0.030155 | 0.068589 | 0.040134 |
| Normal | Z | 0.023458 | 0.059016 | 0.029902 |
| Imbalance, intensity 1.0 | X | 0.106912 | 0.172799 | 0.150543 |
| Imbalance, intensity 1.0 | Y | 0.064540 | 0.117207 | 0.090128 |
| Imbalance, intensity 1.0 | Z | 0.057405 | 0.107139 | 0.079902 |

The direct DFT (discrete Fourier transform) is an analysis applied to the
generated samples. It compares them with repeating patterns at candidate
frequencies and estimates how much of each pattern is present. The simulator
signal model is defined in the [simulator specification](../specs/simulator.md#signal-and-condition-behavior);
the DFT is applied afterward and does not generate the signal or calculate
RPM. The reproduction script implements the direct DFT with Python's standard
library to check the spectrum and write
[time-domain](artifacts/EXP-0001-vibration-time.svg) and
[frequency-domain](artifacts/EXP-0001-vibration-spectrum.svg) plots.

A frequency bin is one candidate position on the DFT's frequency grid. The
grid spacing uses the **sampling rate**, not the vibration frequency:
`sampling_rate / sample_count` is `1600 samples/s / 1600 samples = 1 Hz` in
this run. The sampling rate is how often readings are taken; the vibration's
30 Hz frequency is how often its pattern repeats. Since the recording length
is `sample_count / sampling_rate`, bin spacing is also one divided by the
recording length in seconds. Here the 1600 samples at 1600 samples/s make a
one-second recording. Bin 31 tests 31 cycles in that second, while bin 30 tests
30; one extra cycle in one second is 1 Hz. Bin 30 matches the modeled 30 Hz
component. The grid is built from patterns that fit a whole
number of cycles in the window; the actual signal does not have to fit one
exactly. If a signal component falls between bins, its energy can appear across
neighboring bins. A two-second window at the same 1600 samples/s would contain
3200 samples and have 0.5 Hz spacing: adjacent candidates differ by one cycle
over two seconds. In this run the 30 Hz component falls directly on a bin, so
its peak is clear.

## Interpretation

The first settings yield a visible 30 Hz component and distinguish the
configured normal and maximum-intensity imbalance amplitudes in these
synthetic signals. This is a preliminary engineering check, not evidence of
physical condition separation. Alternate duration, sampling-rate, and noise
settings, and temperature/RPM context behavior, remain to be compared before
deciding whether to retain the defaults.

## Limitations

This experiment evaluates engineering usefulness of synthetic signals, not
physical fault-model validity.

## Decision or next action

Keep the defaults provisional. Complete the sampling/noise comparison and
context-generation slice before deciding whether the specification defaults
should change.
