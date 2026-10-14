"""Compare the first three synthetic conditions with fixed-run plots."""

from collections.abc import Sequence
from math import ceil
from pathlib import Path
from typing import Final, Literal

from machinepulse_simulator.models import EffectiveRunConfig
from machinepulse_simulator.telemetry import TelemetryWindow, iter_telemetry_windows

from .plot_utils import PlotSeries, compute_spectrum, render_svg, root_mean_square

type Axis = Literal["x", "y", "z"]

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "docs/experiments/artifacts"
CONDITIONS: Final[tuple[tuple[str, float, str], ...]] = (
    ("normal", 0.0, "#0072b2"),
    ("imbalance", 0.7, "#d55e00"),
    ("overheating", 0.7, "#009e73"),
)
AXES: Final[tuple[Axis, ...]] = ("x", "y", "z")
SAMPLE_RATE_HZ: Final[int] = 1600
WINDOW_DURATION_MS: Final[int] = 1000
WINDOW_COUNT: Final[int] = 4
NOMINAL_RPM: Final[float] = 1800.0
SEED: Final[int] = 1234
TIME_PLOT_DURATION_MS: Final[int] = 100
SPECTRUM_MAX_FREQUENCY_HZ: Final[int] = 100


def _config(condition: str, intensity: float) -> EffectiveRunConfig:
    """Build a resolved fixed configuration for one EXP-0002 scenario.

    Args:
        condition: Selected synthetic operating condition.
        intensity: Configured intensity for the selected condition.

    Returns:
        A validated effective run configuration.
    """
    return EffectiveRunConfig.model_validate(
        {
            "asset_id": "01M00000004D2PF28AQKFF28T5",
            "device_id": "01M000000028T5CY4GNF6YY4HM",
            "run_id": f"run-exp-0002-{condition}",
            "nominal_rpm": NOMINAL_RPM,
            "condition": condition,
            "condition_intensity": intensity,
            "sampling": {
                "rate_hz": SAMPLE_RATE_HZ,
                "window_duration_ms": WINDOW_DURATION_MS,
            },
            "run": {
                "window_count": WINDOW_COUNT,
                "seed": SEED,
                "start_time_utc": "2026-10-14T12:00:00Z",
                "execution_mode": "accelerated",
            },
            "signal": {
                "rotational_peak_m_s2": {"x": 0.05, "y": 0.04, "z": 0.03},
                "rotational_phase_rad": {"x": 0.0, "y": 0.0, "z": 0.0},
                "noise_std_m_s2": 0.01,
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


def _samples(window: TelemetryWindow, axis: Axis) -> Sequence[float]:
    """Return one axis from a validated telemetry window.

    Args:
        window: Telemetry window containing the vibration arrays.
        axis: Axis name to retrieve.

    Returns:
        Ordered acceleration samples for the requested axis.
    """
    vibration = window.measurements.vibration_m_s2
    if axis == "x":
        return vibration.x
    if axis == "y":
        return vibration.y
    return vibration.z


def _scenario_windows() -> dict[str, list[TelemetryWindow]]:
    """Generate the same fixed number of ordered windows for each condition."""
    return {
        condition: list(iter_telemetry_windows(_config(condition, intensity)))
        for condition, intensity, _ in CONDITIONS
    }


def _plot_series(
    windows_by_condition: dict[str, list[TelemetryWindow]],
    *,
    frequency_domain: bool,
) -> list[PlotSeries]:
    """Build X-axis comparison lines in a stable draw order.

    Args:
        windows_by_condition: Ordered telemetry windows for each scenario.
        frequency_domain: Whether to return an amplitude spectrum or time trace.

    Returns:
        Plot series for the first window of each condition.
    """
    series: list[PlotSeries] = []
    # Normal and overheating produce the same seeded vibration. Draw the dashed
    # overheating trace last so its segments show against the solid baseline.
    draw_order = ("normal", "imbalance", "overheating")
    condition_colors = {condition: color for condition, _, color in CONDITIONS}
    dash_patterns = {"normal": "", "imbalance": "", "overheating": "5 3"}
    for condition in draw_order:
        window = windows_by_condition[condition][0]
        values = _samples(window, "x")
        if frequency_domain:
            points = compute_spectrum(
                values,
                sampling_rate_hz=window.sampling.rate_hz,
                max_frequency_hz=SPECTRUM_MAX_FREQUENCY_HZ,
            )
        else:
            sample_limit = ceil(window.sampling.rate_hz * TIME_PLOT_DURATION_MS / 1000)
            points = [
                (sample_index * 1000 / window.sampling.rate_hz, value)
                for sample_index, value in enumerate(values[:sample_limit])
            ]
        series.append(
            (
                condition,
                condition_colors[condition],
                dash_patterns[condition],
                points,
            )
        )
    return series


def _plot_temperature(
    windows_by_condition: dict[str, list[TelemetryWindow]],
) -> list[PlotSeries]:
    """Build temperature context points at each telemetry-window midpoint.

    Args:
        windows_by_condition: Ordered telemetry windows for each scenario.

    Returns:
        One temperature series per condition.
    """
    condition_colors = {condition: color for condition, _, color in CONDITIONS}
    dash_patterns = {"normal": "", "imbalance": "5 3", "overheating": ""}
    series: list[PlotSeries] = []
    for condition, _, _ in CONDITIONS:
        windows = windows_by_condition[condition]
        points = [
            (
                (index + 0.5) * WINDOW_DURATION_MS / 1000,
                window.measurements.temperature_c,
            )
            for index, window in enumerate(windows)
        ]
        series.append(
            (
                condition,
                condition_colors[condition],
                dash_patterns[condition],
                points,
            )
        )
    return series


def _print_summary(
    windows_by_condition: dict[str, list[TelemetryWindow]],
) -> None:
    """Print first-window measurements for the experiment record.

    Args:
        windows_by_condition: Ordered telemetry windows for each scenario.
    """
    print(
        "condition\tintensity\ttemperature_first_c\ttemperature_last_c\t"
        "rpm\trms_x_m_s2\trms_y_m_s2\trms_z_m_s2\t"
        "dominant_x_hz\tdominant_x_amplitude_m_s2\tx_amplitude_at_30_hz_m_s2"
    )
    for condition, intensity, _ in CONDITIONS:
        windows = windows_by_condition[condition]
        first = windows[0]
        last = windows[-1]
        axis_values = {axis: _samples(first, axis) for axis in AXES}
        spectrum = compute_spectrum(
            axis_values["x"],
            sampling_rate_hz=first.sampling.rate_hz,
            max_frequency_hz=SPECTRUM_MAX_FREQUENCY_HZ,
        )
        dominant_frequency, dominant_amplitude = max(
            spectrum, key=lambda point: point[1]
        )
        thirty_hz_amplitude = next(
            amplitude for frequency, amplitude in spectrum if frequency == 30.0
        )
        rms_values = [root_mean_square(axis_values[axis]) for axis in AXES]
        print(
            f"{condition}\t{intensity:.1f}\t"
            f"{first.measurements.temperature_c:.3f}\t"
            f"{last.measurements.temperature_c:.3f}\t"
            f"{first.measurements.rpm:.1f}\t"
            f"{rms_values[0]:.6f}\t{rms_values[1]:.6f}\t{rms_values[2]:.6f}\t"
            f"{dominant_frequency:.1f}\t{dominant_amplitude:.6f}\t"
            f"{thirty_hz_amplitude:.6f}"
        )


def main() -> None:
    """Generate EXP-0002 plots and print reproducible signal summaries."""
    windows_by_condition = _scenario_windows()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    (ARTIFACTS / "EXP-0002-condition-time.svg").write_text(
        render_svg(
            title=f"Synthetic X-axis vibration, first {TIME_PLOT_DURATION_MS} ms",
            x_label="Time from window start (ms)",
            y_label="Acceleration (m/s²)",
            x_min=0.0,
            x_max=float(TIME_PLOT_DURATION_MS),
            y_min=-0.2,
            y_max=0.2,
            x_ticks=(0, 20, 40, 60, 80, 100),
            y_ticks=(-0.2, -0.1, 0.0, 0.1, 0.2),
            series=_plot_series(windows_by_condition, frequency_domain=False),
        ),
        encoding="utf-8",
    )
    (ARTIFACTS / "EXP-0002-condition-spectrum.svg").write_text(
        render_svg(
            title="Synthetic X-axis vibration amplitude spectrum",
            x_label="Frequency (Hz)",
            y_label="One-sided amplitude (m/s²)",
            x_min=0.0,
            x_max=float(SPECTRUM_MAX_FREQUENCY_HZ),
            y_min=0.0,
            y_max=0.15,
            x_ticks=(0, 20, 40, 60, 80, 100),
            y_ticks=(0.0, 0.03, 0.06, 0.09, 0.12, 0.15),
            series=_plot_series(windows_by_condition, frequency_domain=True),
        ),
        encoding="utf-8",
    )
    (ARTIFACTS / "EXP-0002-condition-context.svg").write_text(
        render_svg(
            title="Synthetic temperature context by window midpoint",
            x_label="Time from run start (s)",
            y_label="Temperature (°C)",
            x_min=0.0,
            x_max=float(WINDOW_COUNT),
            y_min=39.0,
            y_max=48.0,
            x_ticks=(0, 1, 2, 3, 4),
            y_ticks=(40, 42, 44, 46, 48),
            series=_plot_temperature(windows_by_condition),
        ),
        encoding="utf-8",
    )
    _print_summary(windows_by_condition)


if __name__ == "__main__":
    main()
