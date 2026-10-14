# Engineering Experiments

Experiments answer uncertain technical or domain questions with evidence. They should be small, reproducible, and explicit about limitations.

## Running the simulator experiments

From the repository root, install the locked environment once, then run the
experiment task that matches the question:

```sh
mise run setup
mise run simulator:experiment:vibration
mise run simulator:experiment:conditions
```

The first task regenerates the EXP-0001 parameter-sweep plots and prints its
fixed-seed measurements. The second regenerates the EXP-0002 condition plots
and prints the corresponding summaries. Both write curated SVGs to
[`artifacts/`](artifacts/) and use the fixed configurations and commands
recorded in [EXP-0001](EXP-0001-simulator-parameters.md) and
[EXP-0002](EXP-0002-condition-separation.md).

Use the [simulator quickstart](../guides/simulator-quickstart.md) to generate a
reusable telemetry dataset through the CLI. Experiment tasks answer analysis
questions by calling the same simulator generation library directly: EXP-0001
uses [`iter_vibration_windows`](../../tools/simulator/src/machinepulse_simulator/vibration.py),
while EXP-0002 uses
[`iter_telemetry_windows`](../../tools/simulator/src/machinepulse_simulator/telemetry.py),
which builds on that vibration generator. The CLI calls `iter_telemetry_windows`
too, so EXP-0002 shares its full generation path; EXP-0001 calls the lower-level
vibration generator for its controlled signal sweeps. The
[CLI repeatability test](../../tools/simulator/tests/test_cli.py) covers the
separate end-to-end file-generation path. See the experiment records for their
specific setups, results, and limitations.

## When to create an experiment

Use an experiment when the answer is not known from documentation or when a design choice depends on measured behavior. Examples include:

- signal-generation parameters;
- feature usefulness;
- anomaly-model behavior;
- storage layout or batch-size performance;
- event-stream throughput;
- failure recovery;
- simulator-versus-hardware differences; and
- dashboard query behavior.

## Experiment lifecycle

```text
Question → Hypothesis → Setup → Run → Results → Interpretation → Next action
```

A failed hypothesis is a useful result. Do not change parameters without recording the change.

## Reproducibility requirements

Record, when applicable:

- experiment identifier;
- date and environment;
- code revision;
- dataset and generator version;
- configuration and random seed;
- hardware details;
- commands used;
- measurements;
- plots or artifacts; and
- known limitations.

## Naming

Use sequential identifiers and descriptive names:

```text
EXP-0001-vibration-window-size.md
EXP-0002-clickhouse-batch-throughput.md
```

Use the [experiment template](template.md) for new records.
