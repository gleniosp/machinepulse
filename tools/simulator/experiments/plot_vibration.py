"""Generate reproducible time- and frequency-domain vibration plots."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape
from math import ceil, cos, hypot, sin, sqrt, tau
from pathlib import Path
from typing import Final, Literal

from machinepulse_simulator.models import EffectiveRunConfig
from machinepulse_simulator.units import MILLISECONDS_PER_SECOND
from machinepulse_simulator.vibration import (
    SyntheticVibrationWindow,
    iter_vibration_windows,
)

type Point = tuple[float, float]
type PlotSeries = tuple[str, str, str, Sequence[Point]]
type Axis = Literal["x", "y", "z"]

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "docs/experiments/artifacts"
AXES: Final[tuple[Axis, ...]] = ("x", "y", "z")
AXIS_COLORS = {"x": "#0072b2", "y": "#d55e00", "z": "#009e73"}
NORMAL_TRACE_DASH_PATTERN: Final[str] = "6 4"
FIRST_POSITIVE_FREQUENCY_BIN: Final[int] = 1
ONE_SIDED_NON_NYQUIST_AMPLITUDE_SCALE: Final[float] = 2.0
NYQUIST_AMPLITUDE_SCALE: Final[float] = 1.0
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


def _experiment_config(condition: str) -> EffectiveRunConfig:
    """Build the fixed configuration used by EXP-0001's vibration slice.

    Args:
        condition: Either ``normal`` or ``imbalance``.

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
            "sampling": {"rate_hz": 1600, "window_duration_ms": 1000},
            "run": {
                "window_count": 1,
                "seed": 1234,
                "start_time_utc": "2026-10-01T12:00:00Z",
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


def _samples(window: SyntheticVibrationWindow, axis: Axis) -> tuple[float, ...]:
    """Return an axis array from a generated window."""
    vibration = window.vibration_m_s2
    if axis == "x":
        return vibration.x
    if axis == "y":
        return vibration.y
    return vibration.z


def _spectrum(
    samples: Sequence[float], sampling_rate_hz: int, max_frequency_hz: int
) -> list[Point]:
    """Compute a one-sided DFT through the requested frequency limit.

    Frequency bins are spaced by ``sampling_rate_hz / len(samples)``. Only
    positive bins at or below the limit and Nyquist frequency are included.
    """
    sample_count = len(samples)
    frequency_bin_spacing_hz = sampling_rate_hz / sample_count
    highest_one_sided_frequency_bin = sample_count // 2
    last_frequency_bin = min(
        max_frequency_hz * sample_count // sampling_rate_hz,
        highest_one_sided_frequency_bin,
    )
    result: list[Point] = []
    for frequency_bin in range(FIRST_POSITIVE_FREQUENCY_BIN, last_frequency_bin + 1):
        real = 0.0
        imaginary = 0.0
        for sample_index, sample in enumerate(samples):
            angle = tau * frequency_bin * sample_index / sample_count
            real += sample * cos(angle)
            imaginary -= sample * sin(angle)
        amplitude_scale = ONE_SIDED_NON_NYQUIST_AMPLITUDE_SCALE
        if sample_count % 2 == 0 and frequency_bin == highest_one_sided_frequency_bin:
            amplitude_scale = NYQUIST_AMPLITUDE_SCALE
        amplitude = amplitude_scale * hypot(real, imaginary) / sample_count
        frequency_hz = frequency_bin * frequency_bin_spacing_hz
        result.append((frequency_hz, amplitude))
    return result


def _rms(samples: Sequence[float]) -> float:
    """Return the root-mean-square acceleration for one axis."""
    return sqrt(sum(sample * sample for sample in samples) / len(samples))


def _plot_svg(
    *,
    title: str,
    x_label: str,
    y_label: str,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    x_ticks: Sequence[float],
    y_ticks: Sequence[float],
    series: Sequence[PlotSeries],
) -> str:
    """Render a small, self-contained SVG line chart using only stdlib code."""
    width, height = 980, 520
    left, right, top, bottom = 92, 760, 70, 422
    plot_width, plot_height = right - left, bottom - top

    def x_pixel(value: float) -> float:
        return left + (value - x_min) * plot_width / (x_max - x_min)

    def y_pixel(value: float) -> float:
        return bottom - (value - y_min) * plot_height / (y_max - y_min)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f"<title>{escape(title)}</title>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        "<style>text{font-family:system-ui,sans-serif;fill:#202124}.grid{stroke:#d9dde3;stroke-width:1}.axis{stroke:#363b42;stroke-width:1.5}.trace{fill:none;stroke-width:2}</style>",
        f'<text x="{width / 2}" y="34" text-anchor="middle" font-size="20" font-weight="600">{escape(title)}</text>',
    ]
    for tick in x_ticks:
        x = x_pixel(tick)
        parts.extend(
            [
                f'<line class="grid" x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{bottom}"/>',
                f'<text x="{x:.2f}" y="{bottom + 24}" text-anchor="middle" font-size="12">{tick:g}</text>',
            ]
        )
    for tick in y_ticks:
        y = y_pixel(tick)
        parts.extend(
            [
                f'<line class="grid" x1="{left}" y1="{y:.2f}" x2="{right}" y2="{y:.2f}"/>',
                f'<text x="{left - 12}" y="{y + 4:.2f}" text-anchor="end" font-size="12">{tick:g}</text>',
            ]
        )
    parts.extend(
        [
            f'<line class="axis" x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}"/>',
            f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{bottom}"/>',
            f'<text x="{(left + right) / 2}" y="{height - 28}" text-anchor="middle" font-size="14">{escape(x_label)}</text>',
            f'<text x="25" y="{(top + bottom) / 2}" text-anchor="middle" font-size="14" transform="rotate(-90 25 {(top + bottom) / 2})">{escape(y_label)}</text>',
        ]
    )
    for index, (label, color, dash, points) in enumerate(series):
        path = " ".join(
            f"{'M' if point_index == 0 else 'L'} {x_pixel(x):.2f} {y_pixel(y):.2f}"
            for point_index, (x, y) in enumerate(points)
        )
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(
            f'<path class="trace" d="{path}" stroke="{color}"{dash_attribute}/>'
        )
        legend_y = top + 18 + index * 25
        parts.extend(
            [
                f'<line x1="785" y1="{legend_y}" x2="820" y2="{legend_y}" stroke="{color}" stroke-width="2"{dash_attribute}/>',
                f'<text x="828" y="{legend_y + 4}" font-size="12">{escape(label)}</text>',
            ]
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


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
            spectrum = _spectrum(
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
                f"{scenario}; axis={axis}; rms_m_s2={_rms(values):.6f}; "
                f"peak_m_s2={max(abs(value) for value in values):.6f}; "
                f"dominant_frequency_hz={dominant_frequency:.1f}; "
                f"dominant_amplitude_m_s2={dominant_amplitude:.6f}"
            )

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "EXP-0001-vibration-time.svg").write_text(
        _plot_svg(
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
        _plot_svg(
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


if __name__ == "__main__":
    main()
