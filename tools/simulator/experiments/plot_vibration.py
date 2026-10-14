"""Generate reproducible time- and frequency-domain vibration plots."""

from math import ceil
from pathlib import Path
from typing import Final, Literal

from machinepulse_simulator.models import EffectiveRunConfig
from machinepulse_simulator.units import MILLISECONDS_PER_SECOND
from machinepulse_simulator.vibration import (
    SyntheticVibrationWindow,
    iter_vibration_windows,
)

from .plot_utils import PlotSeries, compute_spectrum, render_svg, root_mean_square

type Axis = Literal["x", "y", "z"]

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "docs/experiments/artifacts"
AXES: Final[tuple[Axis, ...]] = ("x", "y", "z")
AXIS_COLORS = {"x": "#0072b2", "y": "#d55e00", "z": "#009e73"}
NORMAL_TRACE_DASH_PATTERN: Final[str] = "6 4"
TIME_PLOT_DURATION_MS: Final[int] = 100
TIME_PLOT_ACCELERATION_LIMIT_M_S2: Final[float] = 0.24
TIME_PLOT_TICKS_MS: Final[tuple[int, ...]] = (0, 20, 40, 60, 80, 100)
TIME_PLOT_ACCELERATION_TICKS_M_S2: Final[tuple[float, ...]] = (
    -0.2,
    -0.1,
    0.0,
    0.1,
    0.2,
)
SPECTRUM_MAX_FREQUENCY_HZ: Final[int] = 100
SPECTRUM_FREQUENCY_TICKS_HZ: Final[tuple[int, ...]] = (
    0,
    20,
    40,
    60,
    80,
    100,
)
SPECTRUM_AMPLITUDE_LIMIT_M_S2: Final[float] = 0.17
SPECTRUM_AMPLITUDE_TICKS_M_S2: Final[tuple[float, ...]] = (
    0.0,
    0.04,
    0.08,
    0.12,
    0.16,
)


def _experiment_config(
    condition: str,
    *,
    sampling_rate_hz: int = 1600,
    window_duration_ms: int = 1000,
    noise_std_m_s2: float = 0.01,
) -> EffectiveRunConfig:
    """Build the fixed configuration used by EXP-0001's vibration slice.

    Args:
        condition: Either ``normal`` or ``imbalance``.
        sampling_rate_hz: Samples per second for each axis.
        window_duration_ms: Duration represented by the generated window.
        noise_std_m_s2: Standard deviation of the seeded vibration noise.

    Returns:
        A fully validated one-window signal configuration.
    """
    intensity = 0.0 if condition == "normal" else 1.0
    return EffectiveRunConfig.model_validate(
        {
            "asset_id": "01M00000008NKRJ2NWVVRJ6HB7",
            "device_id": "01M00000006HB7H45BSQQH4D2P",
            "run_id": f"run-exp-0001-{condition}",
            "nominal_rpm": 1800.0,
            "condition": condition,
            "condition_intensity": intensity,
            "sampling": {
                "rate_hz": sampling_rate_hz,
                "window_duration_ms": window_duration_ms,
            },
            "run": {
                "window_count": 1,
                "seed": 1234,
                "start_time_utc": "2026-10-01T12:00:00Z",
                "execution_mode": "accelerated",
            },
            "signal": {
                "rotational_peak_m_s2": {"x": 0.05, "y": 0.04, "z": 0.03},
                "rotational_phase_rad": {"x": 0.0, "y": 0.0, "z": 0.0},
                "noise_std_m_s2": noise_std_m_s2,
                "imbalance_peak_m_s2_at_intensity_1": {
                    "x": 0.10,
                    "y": 0.05,
                    "z": 0.05,
                },
            },
            "temperature": {
                "initial_c": 40.0,
                "overheating_rise_c_at_intensity_1": 10.0,
            },
        }
    )


def _samples(window: SyntheticVibrationWindow, axis: Axis) -> tuple[float, ...]:
    """Return an axis array from a generated window."""
    vibration = window.vibration_m_s2
    if axis == "x":
        return vibration.x
    if axis == "y":
        return vibration.y
    return vibration.z


def _signal_summary(
    condition: str,
    *,
    sampling_rate_hz: int,
    window_duration_ms: int,
    noise_std_m_s2: float,
) -> tuple[float, float, float, float]:
    """Measure X-axis RMS, peak, dominant frequency, and amplitude.

    Args:
        condition: ``normal`` or ``imbalance``.
        sampling_rate_hz: Samples per second for each axis.
        window_duration_ms: Duration represented by the generated window.
        noise_std_m_s2: Standard deviation of the seeded vibration noise.

    Returns:
        RMS, absolute peak, dominant frequency, and dominant amplitude.
    """
    config = _experiment_config(
        condition,
        sampling_rate_hz=sampling_rate_hz,
        window_duration_ms=window_duration_ms,
        noise_std_m_s2=noise_std_m_s2,
    )
    window = next(iter_vibration_windows(config))
    values = _samples(window, "x")
    spectrum = compute_spectrum(
        values,
        sampling_rate_hz=sampling_rate_hz,
        max_frequency_hz=SPECTRUM_MAX_FREQUENCY_HZ,
    )
    dominant_frequency, dominant_amplitude = max(spectrum, key=lambda point: point[1])
    return (
        root_mean_square(values),
        max(abs(value) for value in values),
        dominant_frequency,
        dominant_amplitude,
    )


def _print_parameter_sweep() -> None:
    """Print fixed-seed, one-factor-at-a-time parameter comparisons."""
    settings = (
        ("rate_hz", (400, 800, 1600), 1000, 0.01),
        ("window_duration_ms", (250, 500, 1000), 1600, 0.01),
        ("noise_std_m_s2", (0.005, 0.01, 0.02), 1600, 0.01),
    )
    print("EXP-0001 parameter comparison (fixed seed 1234, X axis)")
    print(
        "parameter\tvalue\tcondition\trms_m_s2\tpeak_m_s2\t"
        "dominant_frequency_hz\tdominant_amplitude_m_s2"
    )
    for parameter, values, default_rate, default_noise in settings:
        for value in values:
            rate = int(value) if parameter == "rate_hz" else default_rate
            duration = int(value) if parameter == "window_duration_ms" else 1000
            noise = float(value) if parameter == "noise_std_m_s2" else default_noise
            for condition in ("normal", "imbalance"):
                rms, peak, dominant_frequency, dominant_amplitude = _signal_summary(
                    condition,
                    sampling_rate_hz=rate,
                    window_duration_ms=duration,
                    noise_std_m_s2=noise,
                )
                print(
                    f"{parameter}\t{value}\t{condition}\t{rms:.6f}\t{peak:.6f}\t"
                    f"{dominant_frequency:.1f}\t{dominant_amplitude:.6f}"
                )


def main() -> None:
    """Generate the EXP-0001 vibration plots and print signal summaries."""
    normal = next(iter_vibration_windows(_experiment_config("normal")))
    imbalance = next(iter_vibration_windows(_experiment_config("imbalance")))
    windows = {"normal": normal, "imbalance at intensity 1.0": imbalance}
    colors = AXIS_COLORS
    time_series: list[PlotSeries] = []
    frequency_series: list[PlotSeries] = []

    for scenario, window in windows.items():
        sampling_rate_hz = window.sampling.rate_hz
        # Include samples with timestamps before the plotted duration ends.
        time_sample_count = ceil(
            sampling_rate_hz * TIME_PLOT_DURATION_MS / MILLISECONDS_PER_SECOND
        )
        for axis in AXES:
            values = _samples(window, axis)
            is_imbalance = scenario.startswith("imbalance")
            dash = "" if is_imbalance else NORMAL_TRACE_DASH_PATTERN
            label = f"{axis.upper()} {scenario}"
            time_points = [
                (
                    sample_index / sampling_rate_hz * MILLISECONDS_PER_SECOND,
                    value,
                )
                for sample_index, value in enumerate(values[:time_sample_count])
            ]
            time_series.append((label, colors[axis], dash, time_points))
            spectrum = compute_spectrum(
                values,
                sampling_rate_hz=sampling_rate_hz,
                max_frequency_hz=SPECTRUM_MAX_FREQUENCY_HZ,
            )
            series_label = f"{axis.upper()} {scenario}"
            frequency_series.append((series_label, colors[axis], dash, spectrum))

            dominant_frequency, dominant_amplitude = max(
                spectrum, key=lambda item: item[1]
            )
            print(
                f"{scenario}; axis={axis}; rms_m_s2={root_mean_square(values):.6f}; "
                f"peak_m_s2={max(abs(value) for value in values):.6f}; "
                f"dominant_frequency_hz={dominant_frequency:.1f}; "
                f"dominant_amplitude_m_s2={dominant_amplitude:.6f}"
            )

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "EXP-0001-vibration-time.svg").write_text(
        render_svg(
            title=f"Synthetic vibration, first {TIME_PLOT_DURATION_MS} ms",
            x_label="Time from window start (ms)",
            y_label="Acceleration (m/s²)",
            x_min=0.0,
            x_max=TIME_PLOT_DURATION_MS,
            y_min=-TIME_PLOT_ACCELERATION_LIMIT_M_S2,
            y_max=TIME_PLOT_ACCELERATION_LIMIT_M_S2,
            x_ticks=TIME_PLOT_TICKS_MS,
            y_ticks=TIME_PLOT_ACCELERATION_TICKS_M_S2,
            series=time_series,
        ),
        encoding="utf-8",
    )
    (ARTIFACTS / "EXP-0001-vibration-spectrum.svg").write_text(
        render_svg(
            title="Synthetic vibration amplitude spectrum",
            x_label="Frequency (Hz)",
            y_label="One-sided amplitude (m/s²)",
            x_min=0.0,
            x_max=SPECTRUM_MAX_FREQUENCY_HZ,
            y_min=0.0,
            y_max=SPECTRUM_AMPLITUDE_LIMIT_M_S2,
            x_ticks=SPECTRUM_FREQUENCY_TICKS_HZ,
            y_ticks=SPECTRUM_AMPLITUDE_TICKS_M_S2,
            series=frequency_series,
        ),
        encoding="utf-8",
    )
    _print_parameter_sweep()


if __name__ == "__main__":
    main()
