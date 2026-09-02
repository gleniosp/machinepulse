# Engineering Experiments

Experiments answer uncertain technical or domain questions with evidence. They should be small, reproducible, and explicit about limitations.

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
