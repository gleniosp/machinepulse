"""Tests for the EXP-0001 vibration spectrum calculation."""

import pytest

from experiments.plot_vibration import _spectrum


def test_spectrum_uses_bin_spacing_to_limit_frequency_in_hertz() -> None:
    """A four-sample window at 8 Hz has bins spaced 2 Hz apart."""
    spectrum = _spectrum((1.0, 0.0, -1.0, 0.0), sampling_rate_hz=8, max_frequency_hz=3)

    assert len(spectrum) == 1
    assert spectrum[0][0] == pytest.approx(2.0)
    assert spectrum[0][1] == pytest.approx(1.0)


def test_spectrum_uses_one_sided_scale_at_nyquist() -> None:
    """An even-length window does not double the Nyquist amplitude."""
    spectrum = _spectrum((1.0, -1.0) * 4, sampling_rate_hz=8, max_frequency_hz=4)

    assert spectrum[-1][0] == pytest.approx(4.0)
    assert spectrum[-1][1] == pytest.approx(1.0)
