"""Small standard-library helpers for reproducible SVG experiment plots."""

from collections.abc import Sequence
from html import escape
from math import cos, hypot, sin, sqrt, tau

type Point = tuple[float, float]
type PlotSeries = tuple[str, str, str, Sequence[Point]]

FIRST_POSITIVE_FREQUENCY_BIN = 1
ONE_SIDED_NON_NYQUIST_AMPLITUDE_SCALE = 2.0
NYQUIST_AMPLITUDE_SCALE = 1.0


def compute_spectrum(
    samples: Sequence[float], sampling_rate_hz: int, max_frequency_hz: int
) -> list[Point]:
    """Compute a one-sided direct DFT through the requested frequency limit.

    Frequency bins are spaced by ``sampling_rate_hz / len(samples)``. Only
    positive bins at or below the limit and Nyquist frequency are included.

    Args:
        samples: Ordered values for a single signal window.
        sampling_rate_hz: Number of samples taken per second.
        max_frequency_hz: Highest positive frequency to return.

    Returns:
        Frequency and one-sided amplitude pairs in ascending order.
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


def root_mean_square(samples: Sequence[float]) -> float:
    """Return the root-mean-square value for a non-empty sample sequence.

    Args:
        samples: Ordered numeric values.

    Returns:
        The square root of the mean squared value.
    """
    return sqrt(sum(sample * sample for sample in samples) / len(samples))


def render_svg(
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
    """Render a self-contained SVG line chart using only standard-library code.

    Args:
        title: Chart title.
        x_label: Horizontal-axis label.
        y_label: Vertical-axis label.
        x_min: Minimum horizontal-axis value.
        x_max: Maximum horizontal-axis value.
        y_min: Minimum vertical-axis value.
        y_max: Maximum vertical-axis value.
        x_ticks: Horizontal-axis tick positions.
        y_ticks: Vertical-axis tick positions.
        series: Labeled, colored data series and optional dash patterns.

    Returns:
        Complete SVG markup with a trailing newline.
    """
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
