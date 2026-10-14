"""End-to-end tests for stable simulator CLI output."""

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from machinepulse_simulator.cli import main


def _scenario_configs(effective_config: dict[str, Any]) -> list[dict[str, Any]]:
    """Return small fixed-seed runs for all initial simulator conditions.

    Args:
        effective_config: Shared resolved simulator test configuration.

    Returns:
        Independent mutable configurations for the three initial conditions.
    """
    scenarios = (("normal", 0.0), ("imbalance", 0.7), ("overheating", 0.7))
    configs: list[dict[str, Any]] = []
    for condition, intensity in scenarios:
        config = deepcopy(effective_config)
        config["condition"] = condition
        config["condition_intensity"] = intensity
        config["nominal_rpm"] = 600.0
        config["sampling"] = {"rate_hz": 128, "window_duration_ms": 1000}
        config["run"]["window_count"] = 4
        config["run_id"] = f"repeatability-{condition}"
        configs.append(config)
    return configs


def _read_json_lines(path: Path) -> list[dict[str, Any]]:
    """Read a UTF-8 JSON-lines file into ordered records.

    Args:
        path: JSON-lines file to read.

    Returns:
        Parsed records in file order.
    """
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_full_runs_repeat_identically_for_all_initial_conditions(
    effective_config: dict[str, Any], tmp_path: Path
) -> None:
    """Repeat complete CLI runs and preserve ordered, separately labeled output."""
    config_path = tmp_path / "runs.json"
    config_path.write_text(
        json.dumps(_scenario_configs(effective_config)), encoding="utf-8"
    )
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"

    assert (
        main(
            [
                "generate",
                "--config",
                str(config_path),
                "--output-dir",
                str(first_output),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "generate",
                "--config",
                str(config_path),
                "--output-dir",
                str(second_output),
            ]
        )
        == 0
    )

    expected_conditions = ("normal", "imbalance", "overheating")
    for run_number, condition in enumerate(expected_conditions, start=1):
        first_run = first_output / f"run-{run_number:03d}"
        second_run = second_output / f"run-{run_number:03d}"
        for filename in ("manifest.json", "telemetry.jsonl", "ground-truth.jsonl"):
            assert (first_run / filename).read_bytes() == (
                second_run / filename
            ).read_bytes()

        telemetry = _read_json_lines(first_run / "telemetry.jsonl")
        sidecar = _read_json_lines(first_run / "ground-truth.jsonl")
        assert [event["sequence"] for event in telemetry] == [0, 1, 2, 3]
        assert [event["event_id"] for event in telemetry] == [
            record["event_id"] for record in sidecar
        ]
        assert all("condition" not in event for event in telemetry)
        assert all("condition_intensity" not in event for event in telemetry)
        assert {record["condition"] for record in sidecar} == {condition}
        assert {record["condition_intensity"] for record in sidecar} == {
            0.0 if condition == "normal" else 0.7
        }
