# Simulator Quickstart

The simulator gives contributors a repeatable source of synthetic motor
telemetry before physical hardware is available. Use it to inspect the
producer-facing contract and prepare small inputs for downstream development.
The synthetic conditions are engineering examples, not validated fault models
or diagnoses; see the [product vision](../product/vision.md) and
[simulator specification](../specs/simulator.md) for the project rationale and
model limits.

## Run the example

To run without installing Python, Pixi, or mise on the host, use the
[Docker quickstart](docker-quickstart.md#generate-a-dataset).

From the repository root, install the locked environment once and run the
canonical example:

```sh
mise run setup
mise run simulator:run generate \
  --config tools/simulator/examples/runs.v1.json
```

Each invocation creates its own UTC-timestamped directory under the ignored
`simulator-output/` folder, so earlier outputs remain available. To choose an
exact destination instead, pass `--output-dir PATH`; that path must not already
exist. Use a path under `/tmp` to keep output outside the checkout. For the CLI
options and file-generation guarantees, see the
[CLI and generated-output contract](../specs/simulator.md#cli-and-generated-output-contract).

## Choose and update examples

The canonical [multi-run configuration](../../tools/simulator/examples/runs.v1.json)
contains one two-window run for each supported initial condition: `normal`,
`imbalance`, and `overheating`. Shared sampling and signal settings make the
condition differences easier to inspect; distinct IDs and seeds keep event
identities and generated noise reproducible. The short runs make a quick local
walkthrough, not a parameter evaluation; use the linked experiments for
evidence about signal defaults and condition separation. The
[experiment guide](../experiments/README.md#running-the-simulator-experiments)
explains how to rerun EXP-0001 and EXP-0002 and how those analyses relate to the
CLI dataset-generation path.

Update this canonical file when changing the small end-to-end example or adding
another supported condition. Add a separate configuration only for a distinct
use, such as a longer experiment or a real-time pacing demonstration. The
[simulator specification](../specs/simulator.md) remains the owner of field
meanings, constraints, and defaults.

## Inspect the output

Each configured run gets a numbered directory. The exact directory layout and
generation guarantees are owned by the
[output contract](../specs/simulator.md#cli-and-generated-output-contract).
Open the files there to inspect or use the run:

- `telemetry.jsonl` contains the generated `telemetry.v1` events. It is useful
  for inspecting or preparing contract-compatible input for downstream
  development.
- `ground-truth.jsonl` contains the known synthetic condition and intensity for
  each event ID. Use it to evaluate behavior against a controlled simulator
  input; it is not a model prediction or an industrial diagnosis.
- `manifest.json` records the effective configuration, seed, generator version,
  and source revision state so the run can be reproduced and traced.

The simulator currently writes local files. It does not publish to MQTT or
automatically feed the gateway. The architecture's simulator/edge-to-MQTT-to-
gateway path is the intended integration; telemetry fields are governed by the
[producer-facing contract](../specs/telemetry-contract.md), and component
responsibilities are described in [runtime boundaries](../architecture/runtime-boundaries.md)
and the [data flow](../architecture/data-flow.md).

## Keep useful artifacts

Generated runs under the root `simulator-output/` directory are ignored by
Git. Keep the compact configuration example, golden test fixtures, and curated
experiment evidence versioned in their owning locations. Routine generated
JSONL is useful for local inspection and downstream development; preserve a run
only when it supports a documented experiment or fixture, with its manifest
and reproducibility context.
