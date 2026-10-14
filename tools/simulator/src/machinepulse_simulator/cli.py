"""Command-line interface for generating reproducible simulator datasets."""

import argparse
import json
import shutil
import sys
import tempfile
import time
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from machinepulse_simulator.models import EffectiveRunConfig
from machinepulse_simulator.reproducibility import (
    GENERATOR_VERSION,
    ReproducibilityError,
    create_ground_truth_record,
    create_run_manifest,
    resolve_source_revision,
    serialize_json,
)
from machinepulse_simulator.telemetry import (
    TelemetryValidationError,
    iter_telemetry_windows,
    serialize_telemetry,
)


class SimulatorCLIError(ValueError):
    """Raised when simulator CLI input or output cannot be handled."""


def _load_run_configs(path: Path) -> list[EffectiveRunConfig]:
    """Read and validate one or more effective run configurations.

    The file may contain one effective configuration, a JSON array of
    configurations, or an object with a single ``runs`` array property.

    Args:
        path: JSON configuration file path.

    Returns:
        The validated configurations in file order.

    Raises:
        SimulatorCLIError: If the file is unreadable or contains invalid input.
    """
    try:
        with path.open(encoding="utf-8") as config_file:
            payload: Any = json.load(config_file)
    except OSError as exc:
        raise SimulatorCLIError(f"cannot read configuration {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SimulatorCLIError(
            f"configuration {path} is not valid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    if isinstance(payload, dict) and "runs" in payload:
        if set(payload) != {"runs"}:
            raise SimulatorCLIError(
                "a multi-run configuration may contain only the 'runs' property"
            )
        raw_configs = payload["runs"]
        if not isinstance(raw_configs, list):
            raise SimulatorCLIError("configuration 'runs' must be a JSON array")
    elif isinstance(payload, list):
        raw_configs = payload
    else:
        raw_configs = [payload]

    if not raw_configs:
        raise SimulatorCLIError("configuration must contain at least one run")

    configs: list[EffectiveRunConfig] = []
    for index, raw_config in enumerate(raw_configs, start=1):
        try:
            configs.append(EffectiveRunConfig.model_validate(raw_config))
        except ValidationError as exc:
            details = "; ".join(
                f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
                for error in exc.errors()
            )
            raise SimulatorCLIError(
                f"invalid run configuration #{index}: {details}"
            ) from exc

    event_identities = [(config.device_id, config.run_id) for config in configs]
    if len(set(event_identities)) != len(event_identities):
        raise SimulatorCLIError(
            "each run must have a unique (device_id, run_id) event identity"
        )
    return configs


def _write_line(file_path: Path, value: str) -> None:
    """Write one UTF-8 JSON record with a stable LF line ending.

    Args:
        file_path: Destination file, which must not already exist.
        value: Compact serialized JSON record.
    """
    with file_path.open("x", encoding="utf-8", newline="\n") as output_file:
        output_file.write(value)
        output_file.write("\n")


def _generate_run(
    config: EffectiveRunConfig,
    manifest: dict[str, object],
    output_dir: Path,
    run_number: int,
) -> tuple[Path, int, float, float]:
    """Generate one run into a staging directory and publish it atomically.

    Args:
        config: Validated effective run configuration.
        manifest: Reproducibility manifest for the run.
        output_dir: New output root created for this invocation.
        run_number: One-based position of this run in the configuration file.

    Returns:
        The committed run directory, window count, elapsed seconds, and maximum
        observed release lateness in seconds.

    Raises:
        SimulatorCLIError: If generation or serialization fails.
    """
    run_dir = output_dir / f"run-{run_number:03d}"
    try:
        staging_dir = Path(
            tempfile.mkdtemp(prefix=f".run-{run_number:03d}-", dir=output_dir)
        )
    except OSError as exc:
        raise SimulatorCLIError(
            f"could not create a staging directory for run {config.run_id!r}: {exc}"
        ) from exc

    telemetry_path = staging_dir / "telemetry.jsonl"
    ground_truth_path = staging_dir / "ground-truth.jsonl"
    manifest_path = staging_dir / "manifest.json"
    started = 0.0
    window_count = 0
    maximum_lateness = 0.0

    try:
        _write_line(manifest_path, serialize_json(manifest))
        with (
            telemetry_path.open("x", encoding="utf-8", newline="\n") as telemetry_file,
            ground_truth_path.open(
                "x", encoding="utf-8", newline="\n"
            ) as ground_truth_file,
        ):
            started = time.monotonic()
            window_duration_seconds = config.sampling.window_duration_ms / 1000
            for window in iter_telemetry_windows(config):
                if config.run.execution_mode == "real_time":
                    deadline = started + window.sequence * window_duration_seconds
                    remaining = deadline - time.monotonic()
                    if remaining > 0:
                        time.sleep(remaining)
                    maximum_lateness = max(
                        maximum_lateness, max(0.0, time.monotonic() - deadline)
                    )

                telemetry_file.write(serialize_telemetry(window))
                telemetry_file.write("\n")
                sidecar = create_ground_truth_record(window.event_id, manifest)
                ground_truth_file.write(serialize_json(sidecar))
                ground_truth_file.write("\n")
                window_count += 1

        elapsed = time.monotonic() - started
        staging_dir.rename(run_dir)
        return run_dir, window_count, elapsed, maximum_lateness
    except Exception as exc:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise SimulatorCLIError(
            f"run {config.run_id!r} failed before its output was committed: {exc}"
        ) from exc


def _create_output_dir(requested_dir: Path | None) -> Path:
    """Create a new invocation output directory.

    If no path is requested, create a unique UTC-timestamped directory under
    ``simulator-output`` in the current working directory.

    Args:
        requested_dir: Optional exact output directory selected by the caller.

    Returns:
        The newly created output directory.

    Raises:
        SimulatorCLIError: If the directory cannot be created without replacing
            existing output.
    """
    if requested_dir is not None:
        try:
            requested_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise SimulatorCLIError(
                f"output directory already exists: {requested_dir}; "
                "choose a new path to avoid overwriting prior output"
            ) from exc
        except OSError as exc:
            raise SimulatorCLIError(
                f"cannot create output directory {requested_dir}: {exc}"
            ) from exc
        return requested_dir

    output_parent = Path("simulator-output")
    try:
        output_parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SimulatorCLIError(
            f"cannot create default output directory {output_parent}: {exc}"
        ) from exc

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = 0
    while True:
        suffix_text = f"-{suffix:03d}" if suffix else ""
        output_dir = output_parent / f"{timestamp}{suffix_text}"
        try:
            output_dir.mkdir(exist_ok=False)
        except FileExistsError:
            suffix += 1
        except OSError as exc:
            raise SimulatorCLIError(
                f"cannot create default output directory {output_dir}: {exc}"
            ) from exc
        else:
            return output_dir


def _build_parser() -> argparse.ArgumentParser:
    """Build the simulator command parser.

    Returns:
        The configured command-line parser.
    """
    parser = argparse.ArgumentParser(
        prog="machinepulse-sim",
        description=(
            "Generate contract-validated synthetic motor telemetry and a "
            "separate ground-truth sidecar."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser(
        "generate", help="generate one or more configured motor runs"
    )
    generate.add_argument(
        "--config",
        required=True,
        type=Path,
        help="JSON effective run config, array, or object containing a 'runs' array",
    )
    generate.add_argument(
        "--output-dir",
        type=Path,
        metavar="PATH",
        help=(
            "exact new output directory (default: unique UTC-timestamped "
            "directory under simulator-output)"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the simulator command-line interface.

    Args:
        argv: Optional command-line arguments, excluding the executable name.

    Returns:
        Process exit status, where zero indicates success.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        configs = _load_run_configs(args.config)
        code_revision, working_tree_dirty = resolve_source_revision()
        manifests = [
            create_run_manifest(
                config.model_dump(mode="json"),
                code_revision=code_revision,
                working_tree_dirty=working_tree_dirty,
                generator_version=GENERATOR_VERSION,
            )
            for config in configs
        ]

        output_dir = _create_output_dir(args.output_dir)

        completed: list[Path] = []
        try:
            for run_number, (config, manifest) in enumerate(
                zip(configs, manifests, strict=True), start=1
            ):
                run_dir, window_count, elapsed, maximum_lateness = _generate_run(
                    config, manifest, output_dir, run_number
                )
                completed.append(run_dir)
                print(
                    f"Generated {window_count} telemetry windows for "
                    f"{config.run_id!r} in {run_dir} "
                    f"({config.run.execution_mode}; {elapsed:.3f}s; "
                    f"maximum release lateness {maximum_lateness:.3f}s)."
                )
        except SimulatorCLIError as exc:
            if completed:
                committed = ", ".join(str(path) for path in completed)
                raise SimulatorCLIError(
                    f"{exc}; earlier complete run outputs remain at: {committed}"
                ) from exc
            try:
                output_dir.rmdir()
            except OSError:
                pass
            raise

        print(f"Run manifest and JSONL outputs are in {output_dir}.")
        return 0
    except (
        OSError,
        SimulatorCLIError,
        ReproducibilityError,
        TelemetryValidationError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
