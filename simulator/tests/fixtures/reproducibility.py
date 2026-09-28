"""Reusable simulator input and golden-output test fixtures."""

from pathlib import Path
from typing import Any

import pytest

FIXTURE_DIR = Path(__file__).parent


@pytest.fixture
def effective_config() -> dict[str, Any]:
    """Provide a fixed, fully resolved imbalance-run configuration.

    Returns:
        A fresh simulator configuration for each test.
    """
    return {
        "asset_id": "asset-0001",
        "condition": "imbalance",
        "condition_intensity": 0.7,
        "device_id": "simulator-0001",
        "nominal_rpm": 1800.0,
        "run": {
            "execution_mode": "accelerated",
            "seed": 1234,
            "start_time_utc": "2026-09-24T12:00:00Z",
            "window_count": 10,
        },
        "run_id": "run-0001",
        "sampling": {"rate_hz": 1600, "window_duration_ms": 1000},
        "signal": {
            "imbalance_peak_m_s2_at_intensity_1": {
                "x": 0.1,
                "y": 0.05,
                "z": 0.05,
            },
            "noise_std_m_s2": 0.01,
            "rotational_peak_m_s2": {"x": 0.05, "y": 0.04, "z": 0.03},
            "rotational_phase_rad": {"x": 0.0, "y": 0.0, "z": 0.0},
        },
        "temperature": {
            "initial_c": 40.0,
            "overheating_rise_c_at_intensity_1": 10.0,
        },
    }


def _read_json_fixture(name: str) -> str:
    """Read a golden JSON file from this fixture directory.

    Args:
        name: Golden fixture filename.

    Returns:
        Exact fixture contents without the final newline.
    """
    return (FIXTURE_DIR / name).read_text(encoding="utf-8").rstrip("\n")


@pytest.fixture
def run_manifest_json() -> str:
    """Provide the canonical run-manifest JSON fixture.

    Returns:
        Exact expected serialized manifest.
    """
    return _read_json_fixture("run-manifest.v1.json")


@pytest.fixture
def ground_truth_json() -> str:
    """Provide the canonical ground-truth JSON fixture.

    Returns:
        Exact expected serialized sidecar record.
    """
    return _read_json_fixture("ground-truth.v1.json")
