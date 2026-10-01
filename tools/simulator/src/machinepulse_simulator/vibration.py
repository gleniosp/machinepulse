"""Deterministic synthetic vibration window generation."""

from collections.abc import Iterator
from dataclasses import dataclass
from math import sin, tau
from random import Random
from typing import Literal

from machinepulse_simulator.domain import ImbalanceCondition
from machinepulse_simulator.models import EffectiveRunConfig
from machinepulse_simulator.reproducibility import GENERATOR_VERSION
from machinepulse_simulator.units import SECONDS_PER_MINUTE


@dataclass(frozen=True, slots=True)
class VibrationSampling:
    """Sampling metadata for a generated vibration window."""

    rate_hz: int
    sample_count: int
    window_duration_ms: int


@dataclass(frozen=True, slots=True)
class VibrationAxes:
    """Per-axis acceleration sample arrays in metres per second squared."""

    x: tuple[float, ...]
    y: tuple[float, ...]
    z: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class SyntheticVibrationWindow:
    """A generated vibration window labeled as synthetic."""

    sampling: VibrationSampling
    vibration_m_s2: VibrationAxes
    synthetic: Literal[True] = True
    generator_version: str = GENERATOR_VERSION


def iter_vibration_windows(
    config: EffectiveRunConfig,
) -> Iterator[SyntheticVibrationWindow]:
    """Yield deterministic vibration windows for one configured run.

    The same effective configuration and seed produce the same ordered sample
    values. Rotational phase continues across window boundaries, and only the
    configured imbalance condition adds a vibration component.

    Args:
        config: Fully validated, resolved configuration for the run.

    Yields:
        One synthetic three-axis vibration window at a time.
    """
    sampling_rate_hz = config.sampling.rate_hz
    sample_count = config.sampling.sample_count
    window_duration_ms = config.sampling.window_duration_ms
    rotational_frequency_hz = config.nominal_rpm / SECONDS_PER_MINUTE
    random_source = Random(config.run.seed)
    operating_condition = config.operating_condition

    if isinstance(operating_condition, ImbalanceCondition):
        imbalance_peaks = operating_condition.applied_peak_m_s2
    else:
        imbalance_peaks = None

    axis_parameters = (
        (
            config.signal.rotational_peak_m_s2.x,
            config.signal.rotational_phase_rad.x,
            imbalance_peaks.x if imbalance_peaks is not None else 0.0,
        ),
        (
            config.signal.rotational_peak_m_s2.y,
            config.signal.rotational_phase_rad.y,
            imbalance_peaks.y if imbalance_peaks is not None else 0.0,
        ),
        (
            config.signal.rotational_peak_m_s2.z,
            config.signal.rotational_phase_rad.z,
            imbalance_peaks.z if imbalance_peaks is not None else 0.0,
        ),
    )

    for window_index in range(config.run.window_count):
        first_sample_index = window_index * sample_count
        axis_samples = tuple(
            tuple(
                (baseline_peak + imbalance_peak)
                * sin(
                    tau
                    * rotational_frequency_hz
                    * ((first_sample_index + sample_index) / sampling_rate_hz)
                    + phase_rad
                )
                + random_source.gauss(0.0, config.signal.noise_std_m_s2)
                for sample_index in range(sample_count)
            )
            for baseline_peak, phase_rad, imbalance_peak in axis_parameters
        )
        x_samples, y_samples, z_samples = axis_samples
        yield SyntheticVibrationWindow(
            sampling=VibrationSampling(
                rate_hz=sampling_rate_hz,
                sample_count=sample_count,
                window_duration_ms=window_duration_ms,
            ),
            vibration_m_s2=VibrationAxes(
                x=x_samples,
                y=y_samples,
                z=z_samples,
            ),
        )
