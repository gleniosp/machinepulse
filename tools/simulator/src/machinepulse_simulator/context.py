"""Deterministic scalar context generation for synthetic telemetry windows."""

from collections.abc import Iterator
from dataclasses import dataclass
from math import isfinite

from machinepulse_simulator.domain import OverheatingCondition
from machinepulse_simulator.models import EffectiveRunConfig


@dataclass(frozen=True, slots=True)
class SyntheticContextWindow:
    """Temperature and rotational speed associated with one run window.

    ``temperature_c`` is degrees Celsius and ``rpm`` is revolutions per
    minute. ``window_index`` is zero-based and aligns this context with the
    corresponding vibration window.
    """

    window_index: int
    temperature_c: float
    rpm: float


def iter_context_windows(
    config: EffectiveRunConfig,
) -> Iterator[SyntheticContextWindow]:
    """Yield deterministic scalar context for every configured run window.

    Temperature is sampled at each window's midpoint. Only an overheating
    condition changes it; RPM remains at nominal speed for every condition.

    Args:
        config: Fully validated, resolved configuration for the run.

    Yields:
        One scalar temperature and RPM context record per window, in run order.

    Raises:
        ValueError: If the configured temperature values overflow to infinity.
    """
    operating_condition = config.operating_condition
    if isinstance(operating_condition, OverheatingCondition):
        total_temperature_rise_c = operating_condition.applied_temperature_rise_c
    else:
        total_temperature_rise_c = 0.0

    window_count = config.run.window_count
    for window_index in range(window_count):
        midpoint_fraction = (window_index + 0.5) / window_count
        temperature_c = (
            config.temperature.initial_c + total_temperature_rise_c * midpoint_fraction
        )
        if not isfinite(temperature_c):
            raise ValueError(
                "generated temperature must remain finite for every window"
            )
        yield SyntheticContextWindow(
            window_index=window_index,
            temperature_c=temperature_c,
            rpm=config.nominal_rpm,
        )
