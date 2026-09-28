# Simulator Behavior

- **Status:** Draft
- **Version:** 0.1
- **Owner:** Phase 01 implementation
- **Related product requirements:** FR-001 through FR-005, NFR-001, NFR-008, NFR-009, NFR-010
- **Related product document:** [Domain model — Telemetry window](../product/domain-model.md#telemetry-window)
- **Related specifications:** [Telemetry contract](telemetry-contract.md)
- **Related ADR:** [ADR-0001 — Telemetry event identifiers](../adr/0001-telemetry-event-identifiers.md)
- **Related tasks:** [P01-001 — Specify simulator behavior and configuration](../tasks/phase-01-simulated-world.md), [Phase 01 — Simulated industrial world](../tasks/phase-01-simulated-world.md)
- **Related experiments:** [EXP-0001](../experiments/EXP-0001-simulator-parameters.md), [EXP-0002](../experiments/EXP-0002-condition-separation.md)

## Purpose and scope

Define the deterministic simulator that produces contract-compliant telemetry
for one or more rotating electric motors before physical hardware is connected.
The simulator is an engineering tool for exercising the telemetry-to-
maintenance path. It is not a validated physical model or a diagnostic
authority.

Version 0.1 models one motor asset type, three vibration axes, temperature,
RPM, and three named conditions: `normal`, `imbalance`, and `overheating`. It
produces telemetry windows and a separate ground-truth sidecar keyed by event
ID.

The motor model contains only a configurable nominal RPM and synthetic signal
parameters. It does not model motor geometry, load, bearings, a validated fault
mechanism, sensor calibration, or hardware timing behavior.

## Run configuration

Each run has the following effective configuration. Values in the Default
column are first implementation settings for synthetic experiments; they are
not physical reference values. [EXP-0001](../experiments/EXP-0001-simulator-parameters.md)
will evaluate the signal defaults before the simulator phase is complete.

| Field | Meaning and constraints | Default |
|---|---|---|
| `asset_id` | Non-empty asset identifier used in telemetry. | Required |
| `device_id` | Non-empty producer identifier used in telemetry. | Required |
| `run_id` | Non-empty identifier for this generated run. Reuse it to reproduce event IDs; use a new value for a distinct run. | Required |
| `nominal_rpm` | Finite, positive motor speed in RPM. It stays constant for the run. | `1800.0` |
| `condition` | One of `normal`, `imbalance`, or `overheating`. | `normal` |
| `condition_intensity` | Finite simulator input from `0.0` through `1.0`. `normal` requires `0.0`; `imbalance` and `overheating` require a value greater than `0.0`. It scales the synthetic condition effect and is recorded as ground truth. | `0.0` for `normal` |
| `sampling.rate_hz` | Positive integer samples per second for each vibration axis. | `1600` |
| `sampling.window_duration_ms` | Positive integer duration represented by every window. | `1000` |
| `run.window_count` | Positive integer number of complete windows; total duration is the count multiplied by the window duration. Partial final windows are not emitted. | Required |
| `run.seed` | Non-negative integer controlling all generated random values. | Required |
| `run.start_time_utc` | UTC time of the first window. If omitted, the simulator resolves it once at run start and records the resolved value in the effective configuration. | Current UTC time |
| `run.execution_mode` | `accelerated` or `real_time`. | `accelerated` |

The number of samples in each vibration axis is derived as:

$$
N_{\mathrm{samples}} = f_s \, \Delta t
$$

Here $f_s$ is the sampling rate in samples per second and $\Delta t$ is the
window duration in seconds. For example, $1600 \, \mathrm{samples/s} \times
1 \, \mathrm{s} = 1600$ samples per axis.

The result must be a positive integer. A configuration whose rate and window
duration do not produce an integral sample count is rejected before output is
generated.

The initial signal and context parameters are configurable as follows:

| Parameter | Meaning and constraints | Initial setting |
|---|---|---|
| `signal.rotational_peak_m_s2` | Non-negative peak amplitude at the rotational frequency, independently set for X, Y, and Z. | X `0.05`, Y `0.04`, Z `0.03` |
| `signal.rotational_phase_rad` | Finite phase offset for each axis' rotational component. | `0.0` on each axis |
| `signal.noise_std_m_s2` | Non-negative standard deviation of zero-mean Gaussian vibration noise, in m/s². | `0.01` |
| `signal.imbalance_peak_m_s2_at_intensity_1` | Non-negative added rotational-frequency peak amplitude per axis at condition intensity `1.0`. | X `0.10`, Y `0.05`, Z `0.05` |
| `temperature.initial_c` | Finite temperature context at run start, in degrees Celsius. | `40.0` |
| `temperature.overheating_rise_c_at_intensity_1` | Non-negative total linear temperature rise across a full run at condition intensity `1.0`, in degrees Celsius. | `10.0` |

These initial signal values are experiment settings chosen to make controlled
signals inspectable. They are not expected operating ranges for a real motor.
Changing a configured value or seed must be visible in the effective run
configuration and sidecar.

## Configuration example

This JSON example uses a normal run. Field names and units are normative; the
initial amplitudes and sampling defaults remain subject to EXP-0001.

```json
{
  "asset_id": "asset-0001",
  "device_id": "simulator-0001",
  "run_id": "run-0001",
  "nominal_rpm": 1800.0,
  "condition": "normal",
  "condition_intensity": 0.0,
  "sampling": {
    "rate_hz": 1600,
    "window_duration_ms": 1000
  },
  "run": {
    "window_count": 10,
    "seed": 1234,
    "start_time_utc": "2026-09-24T12:00:00Z",
    "execution_mode": "accelerated"
  },
  "signal": {
    "rotational_peak_m_s2": {"x": 0.05, "y": 0.04, "z": 0.03},
    "rotational_phase_rad": {"x": 0.0, "y": 0.0, "z": 0.0},
    "noise_std_m_s2": 0.01,
    "imbalance_peak_m_s2_at_intensity_1": {"x": 0.10, "y": 0.05, "z": 0.05}
  },
  "temperature": {
    "initial_c": 40.0,
    "overheating_rise_c_at_intensity_1": 10.0
  }
}
```

An `imbalance` example changes `condition` to `imbalance` and sets
`condition_intensity` between `0.0` and `1.0`, exclusive of `0.0`. An
`overheating` example does the same with `condition` set to `overheating`.

## Signal and condition behavior

The simulator holds nominal RPM constant during a run. The rotational
frequency is:

$$
f_{\mathrm{rot}} = \frac{\mathrm{RPM}_{\mathrm{nominal}}}{60}
$$

The division converts revolutions per minute to revolutions per second
(hertz). For example, the initial setting of $1800$ RPM gives $30$ Hz. For axis
`j` and sample time `t`, the normal vibration signal is:

$$
a_j(t) = A_j \sin\!\left(2\pi f_{\mathrm{rot}} t + \phi_j\right) + \varepsilon_j(t)
$$

Here is what each term means:

- $a_j(t)$ is the simulated acceleration for axis $j$ at time $t$, measured in
  m/s².
- $A_j$ is the configured peak vibration amplitude for that axis, also in
  m/s².
- $f_{\mathrm{rot}}$ is the motor's rotational frequency in hertz, calculated
  as nominal RPM divided by 60.
- $\phi_j$ is the configured phase offset for axis $j$, in radians.
- $\varepsilon_j(t)$ is seeded random noise for that axis. It has mean zero
  and the configured standard deviation.
- $t$ is seconds elapsed since the run started. It keeps the rotational phase
  continuous across telemetry windows.

The sine term describes a smooth repeating vibration once per motor rotation.
The noise adds small unpredictable variation while the seed keeps the same
configuration repeatable. The model has no unconfigured harmonics, transients,
drift, or load changes.

Conditions modify that baseline as follows:

- **`normal`:** Uses the normal vibration signal and holds temperature at
  `temperature.initial_c`. Condition intensity is `0.0`.
- **`imbalance`:** Adds a rotational-frequency sinusoid on each axis. Its peak
  amplitude is the configured intensity-1 amplitude multiplied by
  `condition_intensity`. It uses the same per-axis phase as the normal
  component. Temperature and RPM remain at their normal context values.
- **`overheating`:** Uses the normal vibration signal and nominal RPM.
  Temperature increases linearly from `temperature.initial_c` to the
  configured intensity-scaled rise by the end of the full run.

The scalar temperature for a window is the model value at the window midpoint.
For an overheating run with `N` windows, window index `k` starting at zero,
condition intensity `I`, initial temperature $T_0$, and the configured full-run
rise $\Delta T_{\max}$, it is:

$$
T_k = T_0 + I \, \Delta T_{\max} \, \frac{k + \frac{1}{2}}{N}
$$

The fraction places the value at the midpoint of window $k$ along the full
run. The setting $I$ scales the synthetic rise: at $I=0.5$, each window's
temperature sits halfway between the starting temperature and the rise used
for $I=1.0$, at the same point in the run.

The scalar RPM for every window is `nominal_rpm`. These equations define
controlled synthetic scenarios; they are not validated signatures of
imbalance, overheating, or normal industrial operation.

## Window timing and identity

For window index `k` starting at zero, the window starts at
`run.start_time_utc + k × window_duration_ms`. The `occurred_at` timestamp is
the UTC time of the first vibration sample in that window. Sample `n` on each
axis is generated at `t = k × window_duration_ms / 1000 + n / rate_hz` seconds
since run start. Windows do not overlap, and the last window ends at the
configured total run duration.

The simulator increments the device-local sequence for each window. Event IDs
are canonical lowercase, hyphenated UUIDs. The simulator generates each one as
a deterministic UUIDv5 in the fixed MachinePulse telemetry namespace
`137bfca0-3f75-56ce-a36c-932f0bc60c36`, derived from the stable event identity
tuple `(device_id, run_id, sequence)`. The UUIDv5 name is the UTF-8 encoding of
the compact JSON array `[device_id, run_id, sequence]`, with non-ASCII
characters emitted directly rather than JSON Unicode escape sequences. This
namespace and tuple encoding must remain stable and be covered by the
repeatability fixture defined for P01-002. Distinct runs use distinct run IDs;
reproducing a run with the same `run_id` and effective configuration reproduces
the same event IDs. A producer keeps an event ID unchanged when it retries
delivery. The identifier format and the roles of UUID and sequence are defined
in the [telemetry contract](telemetry-contract.md) and
[ADR-0001](../adr/0001-telemetry-event-identifiers.md).

Given the same effective configuration, seed, and generator version, runs
produce the same ordered vibration values, scalar context, sequence numbers,
event IDs, and ground-truth records. If `start_time_utc` is omitted, reuse the
resolved timestamp recorded in the effective configuration to reproduce
`occurred_at` values. Real-time pacing changes wall-clock release times only.

## Execution modes

- **`accelerated`:** Generate and release windows as quickly as practical.
  Event timestamps and sequence numbers still follow the configured window
  schedule.
- **`real_time`:** Release the first window immediately and schedule each
  following release one window duration apart, using a monotonic clock for
  pacing. Event timestamps still follow the configured UTC schedule.

In real-time mode, the simulator must not drop or reorder windows when
generation falls behind. It emits a late window immediately, then continues
against the original schedule until it has caught up. It reports observed
delivery lateness in run-level evidence. A late release does not alter the
window's `occurred_at` timestamp.

## Run manifest and ground-truth sidecar

Each run has one JSON manifest, separate from the telemetry windows. Its
`manifest_version` is `machinepulse.run-manifest.v1`; fields are:

| Field | Meaning |
|---|---|
| `manifest_version` | Version of this manifest shape. |
| `run_id` | The run identity from the effective configuration. |
| `generator_version` | Stable simulator behavior identifier, initially `simulator.v1`. Increment it when a change can alter generated output for the same effective configuration and seed. |
| `code_revision` | Full source-control revision used to generate the run, or `null` when unavailable. |
| `working_tree_dirty` | Whether tracked or untracked source changes were present, or `null` when it cannot be determined. |
| `effective_config` | Complete configuration after defaults and `run.start_time_utc` have been resolved. It includes the seed and all values needed to regenerate the run. |

Manifest serialization is UTF-8 JSON with object keys sorted lexicographically,
no insignificant whitespace, and non-finite numbers rejected. It contains no
generation timestamp: identical metadata and effective configuration must
serialize identically.

These fields help identify the exact code used for a run:

- In a Git checkout, `code_revision` is the full commit ID reported by
  `git rev-parse HEAD`. `working_tree_dirty` is `false` when the checkout has no
  changes and `true` when it has tracked edits or untracked files. If it is
  `true`, the commit ID alone does not capture all code that produced the run.
- A packaged build may not include Git metadata. It can provide the source
  commit ID through `MACHINEPULSE_CODE_REVISION`; dirty state may still be
  unknown.
- Use `null` when a value cannot be determined. A null `code_revision` means
  the source version may not be traceable well enough to reproduce the run
  exactly; it is not a placeholder for a revision.

Ground truth is the simulator's record of what scenario it intended to
generate. For each telemetry window, a separate sidecar record keyed by
`event_id` carries the run ID, condition, condition intensity, seed, generator
version, code revision, and effective run configuration needed to reproduce
the window. The sidecar record contains `event_id`, `run_id`, `condition`,
`condition_intensity`, `seed`, `generator_version`, `code_revision`,
`working_tree_dirty`, and `effective_config`. Its `event_id` is the same
deterministic UUID as the corresponding telemetry window. The telemetry event
contains the generated measurements; the sidecar contains the scenario
reference and reproducibility details.

For example, `condition: "imbalance"` says that the simulator applied its
configured imbalance effect, while `condition_intensity: 0.7` says the effect
was scaled to 0.7 of the configured value at intensity 1.0. An experiment can
join the sidecar to telemetry by `event_id` and compare computed features or a
model's result with that reference label. This is how we measure whether an
analysis recognized the scenarios present in synthetic data.

Ground truth is an evaluation reference, not an input feature: production
inference must not receive it when producing a prediction. It also does not
establish that a signal pattern is a validated signature of a real fault or
that a physical machine has the named condition. The manifest shape and
revision semantics above are implemented by
[P01-002](../tasks/phase-01-simulated-world.md).

## Failure behavior

The simulator rejects invalid configuration before generating output. Invalid
values include non-positive RPM, sampling rate, window duration, or window
count; a rate and duration that produce a non-integral sample count; a negative
seed; non-finite numeric parameters; a condition intensity outside `0.0`
through `1.0`; or a condition intensity inconsistent with the selected
condition. Identifiers must be non-empty and start time must be a valid UTC
timestamp.

Serialization or contract-validation failures identify the run and event that
failed. A failed run must not silently present incomplete output as a complete
dataset; the run result must report failure and identify any emitted partial
artifacts.

## Synthetic-data limitations

The simulator is a deterministic signal generator, not a digital twin. The
conditions are hand-defined mathematical changes used to exercise software and
exploratory analysis. They do not reproduce a calibrated motor, establish
fault causality, model machine-to-machine variation, prove that a real sensor
would observe the same signal, or validate an anomaly detector. A visible
difference between generated conditions is not evidence of physical
diagnosability or safety.

## Observability and evidence

Each run should expose or record its run ID, effective configuration, seed,
generator version, code revision, execution mode, window count, elapsed time,
and rejected-window count. Real-time runs also record observed delivery
lateness. Phase 01 evidence includes repeatability comparisons, contract
fixtures, time-domain and frequency-domain plots, results from EXP-0001 and
EXP-0002, and the limitations above.

## Acceptance criteria

- [ ] Configuration, conditions, condition intensity, duration, sampling, seed,
  and execution mode are specified.
- [ ] A fixed seed and effective configuration produce repeatable output.
- [ ] Telemetry and ground truth are separate and associated by event ID.
- [ ] Output conforms to `telemetry.v1` and invalid configuration is rejected.
- [ ] Synthetic-data limitations are visible in documentation and evidence.

## Open questions

- Which initial signal defaults and experiment ranges should be retained after
  EXP-0001?
- Does the midpoint convention for temperature and RPM support signal
  processing, as confirmed by P04-001?
