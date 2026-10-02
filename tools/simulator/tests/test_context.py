"""Tests for deterministic temperature and RPM context generation."""

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from machinepulse_simulator.context import iter_context_windows
from machinepulse_simulator.models import EffectiveRunConfig


def _validated_config(
    effective_config: dict[str, Any],
    *,
    condition: str,
    condition_intensity: float,
    window_count: int = 4,
    temperature_initial_c: float = 40.0,
    temperature_rise_c_at_intensity_1: float = 10.0,
) -> EffectiveRunConfig:
    """Return a fixture config with the requested context parameters.

    Args:
        effective_config: Shared test fixture configuration.
        condition: Operating condition for the generated run.
        condition_intensity: Intensity for the selected condition.
        window_count: Number of scalar context records to generate.
        temperature_initial_c: Temperature at the start of the run.
        temperature_rise_c_at_intensity_1: Full-run rise at intensity 1.0.

    Returns:
        A validated effective run configuration.
    """
    values = deepcopy(effective_config)
    values["condition"] = condition
    values["condition_intensity"] = condition_intensity
    values["run"]["window_count"] = window_count
    values["temperature"]["initial_c"] = temperature_initial_c
    values["temperature"]["overheating_rise_c_at_intensity_1"] = (
        temperature_rise_c_at_intensity_1
    )
    return EffectiveRunConfig.model_validate(values)


@pytest.mark.parametrize(
    ("condition", "condition_intensity"),
    [("normal", 0.0), ("imbalance", 0.7)],
)
def test_non_overheating_conditions_hold_temperature_and_nominal_rpm(
    effective_config: dict[str, Any],
    condition: str,
    condition_intensity: float,
) -> None:
    """Normal and imbalance windows use the configured baseline context."""
    config = _validated_config(
        effective_config,
        condition=condition,
        condition_intensity=condition_intensity,
    )

    windows = tuple(iter_context_windows(config))

    assert [window.window_index for window in windows] == [0, 1, 2, 3]
    assert [window.temperature_c for window in windows] == [40.0] * 4
    assert [window.rpm for window in windows] == [1800.0] * 4


def test_overheating_applies_intensity_scaled_rise_at_window_midpoints(
    effective_config: dict[str, Any],
) -> None:
    """Overheating temperature follows the specified midpoint equation."""
    config = _validated_config(
        effective_config,
        condition="overheating",
        condition_intensity=0.5,
    )

    windows = tuple(iter_context_windows(config))

    assert [window.temperature_c for window in windows] == pytest.approx(
        [40.625, 41.875, 43.125, 44.375]
    )
    assert [window.rpm for window in windows] == [1800.0] * 4


def test_context_is_reproducible_for_the_same_fixed_seed_configuration(
    effective_config: dict[str, Any],
) -> None:
    """Repeating a resolved configuration yields identical ordered context."""
    config = _validated_config(
        effective_config,
        condition="overheating",
        condition_intensity=0.8,
    )

    assert tuple(iter_context_windows(config)) == tuple(iter_context_windows(config))


def test_generated_temperature_must_remain_finite(
    effective_config: dict[str, Any],
) -> None:
    """Finite inputs that overflow during addition fail with a clear reason."""
    values = deepcopy(effective_config)
    values["condition"] = "overheating"
    values["condition_intensity"] = 1.0
    values["run"]["window_count"] = 1
    values["temperature"]["initial_c"] = 1.7e308
    values["temperature"]["overheating_rise_c_at_intensity_1"] = 1.7e308
    config = EffectiveRunConfig.model_validate(values)

    with pytest.raises(ValueError, match="temperature must remain finite"):
        next(iter_context_windows(config))


def test_run_configuration_rejects_non_finite_context_inputs(
    effective_config: dict[str, Any],
) -> None:
    """Configuration validation rejects non-finite temperature parameters."""
    values = deepcopy(effective_config)
    values["temperature"]["initial_c"] = float("inf")

    with pytest.raises(ValidationError):
        EffectiveRunConfig.model_validate(values)
