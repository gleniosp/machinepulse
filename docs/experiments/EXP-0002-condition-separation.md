# EXP-0002 — Synthetic condition separation

- **Status:** Complete
- **Date started:** 2026-10-14
- **Date completed:** 2026-10-14
- **Owner:** Phase 01 implementation
- **Related requirements:** FR-003, FR-005, FR-017, NFR-009
- **Related specifications:** [Simulator behavior](../specs/simulator.md)
- **Related ADRs:**
- **Code revision:** `bb6a3410547ba091aa8796173f356e16b1252168` (working tree included the P01-008 experiment script)
- **Dataset or generator version:** `simulator.v1`

## Question

Do the first three synthetic conditions create different time-, frequency-, or
context-domain evidence under a controlled, reproducible setup, suitable for
exercising downstream processing without implying physical diagnosability?

## Hypothesis

At matched simulator settings, imbalance will change the modeled rotational
vibration amplitude, overheating will change temperature context, and the
overheating vibration will match the normal baseline because this simulator
does not model an overheating vibration effect.

## Setup

Generated four one-second windows for each condition using the same seed
(`1234`), sampling rate (1600 Hz), nominal RPM (1800), initial temperature
(40 °C), and noise standard deviation (0.01 m/s²). The normal run used intensity
0; imbalance and overheating each used intensity 0.7. Each run used an explicit
UTC start time and a distinct run ID. The plots show X-axis vibration from the
first window and the scalar temperature value associated with each window
midpoint. The script derives its condition labels from the run configuration;
condition labels are not fields in `telemetry.v1`.

## Variables

### Controlled variables

- Generator version, seed, RPM, sample rate, window duration, signal settings,
  temperature settings, and start time.

### Independent variables

- Operating condition and condition intensity (normal at 0; imbalance and
  overheating at 0.7).

### Measured variables

- Per-axis RMS, X-axis time waveform and one-sided spectrum, dominant X-axis
  frequency and amplitude, and first/last temperature context values.

## Reproduction command

```text
mise run simulator:experiment:conditions
```

## Results

| Condition | Intensity | Temperature first/last (°C) | RMS X/Y/Z (m/s²) | Dominant X frequency (Hz) | X amplitude at 30 Hz (m/s²) |
|---|---:|---:|---:|---:|---:|
| Normal | 0.0 | 40.000 / 40.000 | 0.037095 / 0.030155 / 0.023458 | 30.0 | 0.050545 |
| Imbalance | 0.7 | 40.000 / 40.000 | 0.085813 / 0.054094 / 0.047004 | 30.0 | 0.120543 |
| Overheating | 0.7 | 40.875 / 46.125 | 0.037095 / 0.030155 / 0.023458 | 30.0 | 0.050545 |

All conditions retained 1800 RPM. Normal and overheating produced identical
vibration samples with the fixed seed. The imbalance scenario raised the X-axis
30 Hz component from 0.050545 to 0.120543 m/s², consistent with the configured
intensity-scaled addition. The overheating scenario changed only the modeled
temperature context, sampled at window midpoints.

The generated figures are [time-domain vibration](artifacts/EXP-0002-condition-time.svg),
[frequency-domain vibration](artifacts/EXP-0002-condition-spectrum.svg), and
[temperature context](artifacts/EXP-0002-condition-context.svg).

## Interpretation

The experiment confirms that the fixed scenarios exercise two separate input
patterns: a stronger rotational vibration component for imbalance and a rising
temperature context for overheating. The overheating case is not identifiable
from vibration in this model alone; its vibration matches normal by design.
This is a useful check of generated features, context association, and
ground-truth separation, not evidence that these signatures distinguish real
motor conditions.

## Limitations

This small experiment uses one seed, one nominal speed, one signal parameter
set, one intensity for each simulated condition, and one motor configuration.
It does not model load variation, sensor placement, installation differences,
transients, or physical fault mechanisms. Its results do not validate a fault
signature, health score, anomaly detector, or maintenance decision.

## Decision or next action

Keep the conditions as controlled synthetic fixtures for downstream contract
and processing work. Keep condition labels in the ground-truth sidecar and out
of production telemetry. Compare generated and physical telemetry only under a
separately reviewed experiment after physical-producer integration.
