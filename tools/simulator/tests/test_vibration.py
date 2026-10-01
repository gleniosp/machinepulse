"""Tests for deterministic three-axis vibration generation."""

from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from machinepulse_simulator.models import EffectiveRunConfig, SamplingConfig
from machinepulse_simulator.reproducibility import GENERATOR_VERSION, serialize_json
from machinepulse_simulator.vibration import iter_vibration_windows

FIXTURES = Path(__file__).parent / "fixtures"


def _validated_config(
    effective_config: dict[str, Any],
    *,
    nominal_rpm: float | None = None,
    condition: str | None = None,
    condition_intensity: float | None = None,
    sampling_rate_hz: int | None = None,
    window_duration_ms: int | None = None,
    window_count: int | None = None,
    seed: int | None = None,
    noise_std_m_s2: float | None = None,
) -> EffectiveRunConfig:
    """Return the fixture config with requested vibration parameters changed.

    Args:
        effective_config: Shared test fixture configuration.
        nominal_rpm: Optional motor speed override.
        condition: Optional operating-condition override.
        condition_intensity: Optional condition intensity override.
        sampling_rate_hz: Optional sampling-rate override.
        window_duration_ms: Optional window-duration override.
        window_count: Optional run window-count override.
        seed: Optional run seed override.
        noise_std_m_s2: Optional vibration noise override.

    Returns:
        A validated copy of the effective run configuration.
    """
    values = deepcopy(effective_config)
    if nominal_rpm is not None:
        values["nominal_rpm"] = nominal_rpm
    if condition is not None:
        values["condition"] = condition
    if condition_intensity is not None:
        values["condition_intensity"] = condition_intensity
    if sampling_rate_hz is not None:
        values["sampling"]["rate_hz"] = sampling_rate_hz
    if window_duration_ms is not None:
        values["sampling"]["window_duration_ms"] = window_duration_ms
    if window_count is not None:
        values["run"]["window_count"] = window_count
    if seed is not None:
        values["run"]["seed"] = seed
    if noise_std_m_s2 is not None:
        values["signal"]["noise_std_m_s2"] = noise_std_m_s2
    return EffectiveRunConfig.model_validate(values)


def test_windows_match_declared_rate_and_sample_count(
    effective_config: dict[str, Any],
) -> None:
    """All axes contain the samples declared by the validated configuration."""
    config = _validated_config(
        effective_config,
        sampling_rate_hz=16,
        window_duration_ms=500,
        window_count=2,
    )

    windows = tuple(iter_vibration_windows(config))

    assert len(windows) == 2
    for window in windows:
        assert window.synthetic is True
        assert window.generator_version == GENERATOR_VERSION
        assert window.sampling.rate_hz == 16
        assert window.sampling.sample_count == 8
        assert window.sampling.window_duration_ms == 500
        assert len(window.vibration_m_s2.x) == 8
        assert len(window.vibration_m_s2.y) == 8
        assert len(window.vibration_m_s2.z) == 8


def test_sampling_rejects_fractional_sample_count() -> None:
    """A sampling interval must represent an integral number of samples."""
    with pytest.raises(ValidationError, match="integral sample count"):
        SamplingConfig(rate_hz=1500, window_duration_ms=1)


def test_rotational_component_uses_nominal_rpm_and_axis_parameters(
    effective_config: dict[str, Any],
) -> None:
    """120 RPM yields a two-hertz component with configured axis peaks."""
    values = deepcopy(effective_config)
    values["condition"] = "normal"
    values["condition_intensity"] = 0.0
    values["nominal_rpm"] = 120.0
    values["sampling"] = {"rate_hz": 240, "window_duration_ms": 1000}
    values["run"]["window_count"] = 1
    values["signal"]["rotational_peak_m_s2"] = {"x": 0.2, "y": 0.0, "z": 0.0}
    values["signal"]["rotational_phase_rad"] = {"x": 0.0, "y": 0.0, "z": 0.0}
    values["signal"]["noise_std_m_s2"] = 0.0
    config = EffectiveRunConfig.model_validate(values)

    window = next(iter_vibration_windows(config))

    assert window.vibration_m_s2.x[30] == pytest.approx(0.2)
    assert window.vibration_m_s2.x[90] == pytest.approx(-0.2)
    assert set(window.vibration_m_s2.y) == {0.0}
    assert set(window.vibration_m_s2.z) == {0.0}


def test_imbalance_adds_its_configured_intensity_scaled_peak(
    effective_config: dict[str, Any],
) -> None:
    """The imbalance signal adds the configured peak at the same phase."""
    values = deepcopy(effective_config)
    values["nominal_rpm"] = 60.0
    values["sampling"] = {"rate_hz": 8, "window_duration_ms": 1000}
    values["run"]["window_count"] = 1
    values["signal"]["rotational_peak_m_s2"] = {"x": 0.1, "y": 0.0, "z": 0.0}
    values["signal"]["imbalance_peak_m_s2_at_intensity_1"] = {
        "x": 0.04,
        "y": 0.0,
        "z": 0.0,
    }
    values["signal"]["noise_std_m_s2"] = 0.0

    normal_values = deepcopy(values)
    normal_values["condition"] = "normal"
    normal_values["condition_intensity"] = 0.0
    imbalance_values = deepcopy(values)
    imbalance_values["condition"] = "imbalance"
    imbalance_values["condition_intensity"] = 0.5

    normal = next(
        iter_vibration_windows(EffectiveRunConfig.model_validate(normal_values))
    )
    imbalance = next(
        iter_vibration_windows(EffectiveRunConfig.model_validate(imbalance_values))
    )

    assert imbalance.vibration_m_s2.x[2] - normal.vibration_m_s2.x[2] == pytest.approx(
        0.02
    )


def test_same_seed_reproduces_all_ordered_values_and_different_seed_changes_noise(
    effective_config: dict[str, Any],
) -> None:
    """Fixed configuration and seed reproduce the complete ordered run."""
    config = _validated_config(
        effective_config,
        sampling_rate_hz=8,
        window_count=2,
        noise_std_m_s2=0.001,
    )
    repeated = _validated_config(
        effective_config,
        sampling_rate_hz=8,
        window_count=2,
        noise_std_m_s2=0.001,
    )
    different_seed = _validated_config(
        effective_config,
        sampling_rate_hz=8,
        window_count=2,
        seed=4321,
        noise_std_m_s2=0.001,
    )

    first_output = tuple(iter_vibration_windows(config))
    repeated_output = tuple(iter_vibration_windows(repeated))
    changed_seed_output = tuple(iter_vibration_windows(different_seed))

    assert first_output == repeated_output
    assert first_output != changed_seed_output


def test_noise_standard_deviation_is_configurable(
    effective_config: dict[str, Any],
) -> None:
    """A zero-noise run removes the seeded random perturbation."""
    without_noise = _validated_config(
        effective_config,
        sampling_rate_hz=8,
        window_count=1,
        noise_std_m_s2=0.0,
    )
    with_noise = _validated_config(
        effective_config,
        sampling_rate_hz=8,
        window_count=1,
        noise_std_m_s2=0.01,
    )

    assert next(iter_vibration_windows(without_noise)) != next(
        iter_vibration_windows(with_noise)
    )


def test_generator_v1_output_matches_golden_vibration_fixture(
    effective_config: dict[str, Any],
) -> None:
    """Keep the initial signal output tied to its recorded generator version."""
    config = _validated_config(
        effective_config,
        sampling_rate_hz=8,
        window_count=1,
    )
    expected = json.loads(
        (FIXTURES / "vibration-window.v1.json").read_text(encoding="utf-8")
    )

    actual = asdict(next(iter_vibration_windows(config)))

    assert json.loads(serialize_json(actual)) == expected


def test_rotational_phase_continues_across_window_boundary(
    effective_config: dict[str, Any],
) -> None:
    """The second window starts at the global run time, not at phase zero."""
    values = deepcopy(effective_config)
    values["condition"] = "normal"
    values["condition_intensity"] = 0.0
    values["nominal_rpm"] = 1830.0
    values["sampling"] = {"rate_hz": 1000, "window_duration_ms": 500}
    values["run"]["window_count"] = 2
    values["signal"]["rotational_peak_m_s2"] = {"x": 0.2, "y": 0.0, "z": 0.0}
    values["signal"]["noise_std_m_s2"] = 0.0
    config = EffectiveRunConfig.model_validate(values)

    first, second = iter_vibration_windows(config)

    assert first.vibration_m_s2.x[0] == pytest.approx(0.0)
    assert second.vibration_m_s2.x[0] == pytest.approx(0.2)


def test_non_imbalance_conditions_do_not_change_the_vibration_formula(
    effective_config: dict[str, Any],
) -> None:
    """Overheating changes temperature context, not this vibration signal."""
    normal_values = deepcopy(effective_config)
    normal_values["condition"] = "normal"
    normal_values["condition_intensity"] = 0.0
    overheating_values = deepcopy(effective_config)
    overheating_values["condition"] = "overheating"
    overheating_values["condition_intensity"] = 0.7
    normal_config = EffectiveRunConfig.model_validate(normal_values)
    overheating_config = EffectiveRunConfig.model_validate(overheating_values)

    assert tuple(iter_vibration_windows(normal_config)) == tuple(
        iter_vibration_windows(overheating_config)
    )
