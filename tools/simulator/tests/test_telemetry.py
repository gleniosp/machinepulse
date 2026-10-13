"""Tests for ``telemetry.v1`` construction, validation, and serialization."""

from copy import deepcopy
from json import loads
from pathlib import Path
from typing import Any

import pytest

from machinepulse_simulator.models import EffectiveRunConfig
from machinepulse_simulator.telemetry import (
    TelemetryValidationError,
    iter_telemetry_windows,
    serialize_telemetry,
    validate_telemetry,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"
INVALID_FIXTURE_CASES = (
    ("missing-device-id.json", "device_id"),
    ("unsupported-schema-version.json", "telemetry.v1"),
    ("noncanonical-event-id.json", "lowercase hyphenated UUID"),
    ("naive-timestamp.json", "timezone information"),
    ("non-utc-timestamp.json", "must use UTC"),
    ("mismatched-axis-count.json", "expected 4"),
    ("inconsistent-window-duration.json", "one sample interval"),
    ("negative-rpm.json", "greater than or equal to 0"),
    ("non-numeric-temperature.json", "finite number"),
)


def _read_json_fixture(path: Path) -> Any:
    """Load a JSON fixture from the simulator test data directory.

    Args:
        path: Fixture path relative to the fixture directory.

    Returns:
        The decoded JSON value.
    """
    return loads(path.read_text(encoding="utf-8"))


def _telemetry_config(
    config_values: dict[str, Any],
    *,
    condition: str,
    condition_intensity: float,
) -> EffectiveRunConfig:
    """Create a small simulator run for contract integration tests.

    Args:
        config_values: Shared effective configuration fixture.
        condition: Selected synthetic operating condition.
        condition_intensity: Intensity for that condition.

    Returns:
        A validated configuration with two four-sample windows.
    """
    values = deepcopy(config_values)
    values["condition"] = condition
    values["condition_intensity"] = condition_intensity
    values["sampling"] = {"rate_hz": 4, "window_duration_ms": 1000}
    values["run"]["window_count"] = 2
    return EffectiveRunConfig.model_validate(values)


def test_valid_telemetry_fixture_validates_and_serializes_canonically() -> None:
    """The checked-in contract fixture is accepted and serializes stably."""
    payload = _read_json_fixture(FIXTURE_DIR / "telemetry.v1.json")

    telemetry = validate_telemetry(payload)
    serialized = serialize_telemetry(telemetry)

    assert telemetry.schema_version == "telemetry.v1"
    assert telemetry.event_id == "550e8400-e29b-41d4-a716-446655440000"
    assert telemetry.occurred_at.isoformat() == "2026-09-24T12:00:00+00:00"
    assert loads(serialized) == telemetry.model_dump(mode="json")
    assert serialized == serialize_telemetry(payload)


@pytest.mark.parametrize(
    ("condition", "condition_intensity"),
    [("normal", 0.0), ("imbalance", 0.7), ("overheating", 0.7)],
)
def test_simulator_windows_are_contract_valid_for_each_condition(
    effective_config: dict[str, Any],
    condition: str,
    condition_intensity: float,
) -> None:
    """All three synthetic conditions produce valid telemetry windows."""
    config = _telemetry_config(
        effective_config,
        condition=condition,
        condition_intensity=condition_intensity,
    )

    telemetry_windows = tuple(iter_telemetry_windows(config))

    assert [window.sequence for window in telemetry_windows] == [0, 1]
    assert [window.occurred_at.isoformat() for window in telemetry_windows] == [
        "2026-09-24T12:00:00+00:00",
        "2026-09-24T12:00:01+00:00",
    ]
    assert [window.event_id for window in telemetry_windows] == [
        window.event_id for window in iter_telemetry_windows(config)
    ]
    for window in telemetry_windows:
        assert window.schema_version == "telemetry.v1"
        assert window.sampling.sample_count == 4
        assert len(window.measurements.vibration_m_s2.x) == 4
        assert len(window.measurements.vibration_m_s2.y) == 4
        assert len(window.measurements.vibration_m_s2.z) == 4
        assert validate_telemetry(window) == window
        assert loads(serialize_telemetry(window))["schema_version"] == "telemetry.v1"


@pytest.mark.parametrize(
    ("fixture_name", "expected_reason"),
    INVALID_FIXTURE_CASES,
)
def test_invalid_payload_fixtures_are_rejected_with_field_reasons(
    fixture_name: str,
    expected_reason: str,
) -> None:
    """Invalid JSON examples fail validation with a useful explanation."""
    payload = _read_json_fixture(FIXTURE_DIR / "telemetry-invalid" / fixture_name)

    with pytest.raises(TelemetryValidationError, match=expected_reason):
        validate_telemetry(payload)


@pytest.mark.parametrize("identifier_field", ["asset_id", "device_id"])
@pytest.mark.parametrize(
    "invalid_ulid",
    [
        pytest.param("01m000000028t5cy4gnf6yy4hm", id="lowercase"),
        pytest.param("01M000000028T5CY4GNF6YY4HI", id="invalid-alphabet"),
        pytest.param("01M000000028T5CY4GNF6YY4H", id="too-short"),
        pytest.param("01M000000028T5CY4GNF6YY4HMM", id="too-long"),
        pytest.param("81M000000028T5CY4GNF6YY4HM", id="overflow"),
        pytest.param(" 01M000000028T5CY4GNF6YY4HM", id="whitespace"),
        pytest.param("device-01M000000028T5CY4GNF6YY4HM", id="prefix"),
        pytest.param(17, id="non-string"),
    ],
)
def test_telemetry_rejects_noncanonical_entity_ulids(
    identifier_field: str, invalid_ulid: object
) -> None:
    """Telemetry entity IDs must match the strict canonical ULID profile."""
    payload = _read_json_fixture(FIXTURE_DIR / "telemetry.v1.json")
    payload[identifier_field] = invalid_ulid

    with pytest.raises(
        TelemetryValidationError, match="must be a canonical uppercase ULID"
    ):
        validate_telemetry(payload)


def test_json_integer_measurements_are_accepted_as_finite_numbers() -> None:
    """JSON integer values are valid numbers for scalar and array measurements."""
    payload = _read_json_fixture(FIXTURE_DIR / "telemetry.v1.json")
    payload["measurements"]["temperature_c"] = 40
    payload["measurements"]["rpm"] = 1800
    payload["measurements"]["vibration_m_s2"]["x"] = [0, 1, -1, 0]

    telemetry = validate_telemetry(payload)

    assert telemetry.measurements.temperature_c == 40.0
    assert telemetry.measurements.rpm == 1800.0
    assert telemetry.measurements.vibration_m_s2.x == [0.0, 1.0, -1.0, 0.0]


def test_non_finite_python_numeric_measurements_are_rejected() -> None:
    """Python NaN values cannot bypass the finite-number contract."""
    payload = _read_json_fixture(FIXTURE_DIR / "telemetry.v1.json")
    payload["measurements"]["vibration_m_s2"]["x"][0] = float("nan")

    with pytest.raises(TelemetryValidationError, match="finite number"):
        validate_telemetry(payload)


def test_sampling_duration_allows_a_difference_smaller_than_one_sample() -> None:
    """The documented duration tolerance is less than one sample interval."""
    payload = _read_json_fixture(FIXTURE_DIR / "telemetry.v1.json")
    payload["sampling"]["window_duration_ms"] = 1100

    telemetry = validate_telemetry(payload)

    assert telemetry.sampling.window_duration_ms == 1100


def test_unknown_payload_fields_are_rejected() -> None:
    """The versioned wire model rejects misspelled or undeclared properties."""
    payload = _read_json_fixture(FIXTURE_DIR / "telemetry.v1.json")
    payload["measurements"]["temperatur_c"] = 40.0

    with pytest.raises(TelemetryValidationError, match="temperatur_c"):
        validate_telemetry(payload)
