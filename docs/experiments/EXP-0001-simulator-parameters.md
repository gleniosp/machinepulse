# EXP-0001 — Simulator parameter ranges

- **Status:** Complete
- **Date started:** 2026-10-01
- **Date completed:** 2026-10-14
- **Owner:** Phase 01 implementation
- **Related requirements:** FR-002, FR-003, FR-004, NFR-001
- **Related specifications:** [Simulator behavior](../specs/simulator.md)
- **Related ADRs:**
- **Code revision:** `bb6a3410547ba091aa8796173f356e16b1252168` (working tree included the P01-008 sweep and plot scripts)
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
as their generators are implemented. Compare normal and imbalance vibration
while changing one of sample rate, window duration, or noise at a time. Use the
time-domain summaries and spectra to select inspectable initial values without
claiming physical validity.

## Variables

### Controlled variables

- Generator version, seed set, nominal RPM, and asset configuration.

### Independent variables

- Sample rate (400, 800, and 1600 Hz), window duration (250, 500, and 1000 ms),
  noise standard deviation (0.005, 0.01, and 0.02 m/s²), and condition (normal
  or intensity-1.0 imbalance). Each comparison changes one signal setting at a
  time from the 1600 Hz, 1000 ms, 0.01 m/s² baseline.

### Measured variables

- RMS/peak summaries, dominant spectral peaks, and qualitative plot
  readability.

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

The one-factor-at-a-time comparison on 2026-10-14 found:

| Setting | Normal X-axis result | Imbalance X-axis result | Observation |
|---|---|---|---|
| Sample rate 400, 800, 1600 Hz; 1000 ms | Dominant 30 Hz amplitude 0.049764–0.050545 m/s² | Dominant 30 Hz amplitude 0.149759–0.150543 m/s² | All three rates put the modeled 30 Hz component on a 1 Hz DFT bin in this synthetic one-second window. |
| Window 250 ms; 1600 Hz | Dominant bin 28 Hz, amplitude 0.034854 m/s² | Dominant bin 28 Hz, amplitude 0.100695 m/s² | The 4 Hz bin spacing does not include 30 Hz and spreads its amplitude across bins. |
| Window 500 ms; 1600 Hz | Dominant 30 Hz amplitude 0.050390 m/s² | Dominant 30 Hz amplitude 0.150390 m/s² | The 2 Hz bin spacing includes 30 Hz. |
| Window 1000 ms; 1600 Hz | Dominant 30 Hz amplitude 0.050545 m/s² | Dominant 30 Hz amplitude 0.150543 m/s² | The 1 Hz bin spacing makes the modeled peak easy to inspect. |
| Noise standard deviation 0.005–0.02 m/s²; 1600 Hz, 1000 ms | X-axis RMS 0.035893–0.041231 m/s²; 30 Hz amplitude 0.050272–0.051099 m/s² | X-axis RMS 0.106374–0.108666 m/s²; 30 Hz amplitude 0.150271–0.151088 m/s² | Higher noise increases time-domain RMS and peak variation; the modeled component remains visible in this fixed one-second comparison. |

Temperature and RPM context are deterministic and were checked separately in
P01-005. Overheating changes the temperature context while retaining the same
seeded vibration as normal. That result is detailed in
[EXP-0002](EXP-0002-condition-separation.md).

## Interpretation

The selected 1600 Hz, 1000 ms, and 0.01 m/s² settings make the synthetic 30 Hz
component easy to inspect. A half-second window also resolves 30 Hz exactly in
this configuration; a quarter-second window does not. All tested rates
preserved the modeled peak, so the 1600 Hz rate is a conservative initial
engineering setting rather than a demonstrated minimum. The noise sweep
increased time-domain variation while leaving the one-second 30 Hz amplitude
near its configured value. These measurements support keeping the current
settings for repeatable engineering examples, not as recommended physical
motor settings.

## Limitations

This experiment evaluates inspectability of deterministic synthetic signals
for one RPM, seed, and set of amplitudes. It does not test real sensor noise,
changing loads, a physical fault model, or diagnostic performance.

## Decision or next action

Retain the configured values as initial synthetic settings in the simulator
specification. No physical operating ranges or diagnostic claims follow from
this experiment. The context slice is recorded in P01-005 and condition
comparison evidence in EXP-0002; later work may revisit these settings against
feature requirements or physical telemetry.
