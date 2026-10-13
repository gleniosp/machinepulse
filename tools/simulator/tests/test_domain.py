"""Unit tests for the simulator's motor and condition domain models."""

import pytest
from pydantic import ValidationError

from machinepulse_simulator.domain import (
    AxisValues,
    ImbalanceCondition,
    MotorConfig,
    NormalCondition,
    NonNegativeAxisValues,
    OverheatingCondition,
    REQUIRED_SENSOR_GROUPS,
)
from machinepulse_simulator.models import EffectiveRunConfig


def test_motor_config_declares_required_v01_sensor_groups() -> None:
    """Default motor models carry each required logical sensor group."""
    motor = MotorConfig(nominal_rpm=1800.0)

    assert motor.nominal_rpm == 1800.0
    assert motor.sensor_groups == REQUIRED_SENSOR_GROUPS


def test_motor_config_allows_group_order_without_omitting_groups() -> None:
    """Group ordering may vary while the required set remains complete."""
    motor = MotorConfig(
        nominal_rpm=1750.0,
        sensor_groups=("rpm", "vibration", "temperature"),
    )

    assert set(motor.sensor_groups) == set(REQUIRED_SENSOR_GROUPS)


@pytest.mark.parametrize("nominal_rpm", [0.0, -1.0, float("nan"), float("inf")])
def test_motor_config_rejects_invalid_nominal_rpm(nominal_rpm: float) -> None:
    """Nominal RPM must be finite and positive."""
    with pytest.raises(ValidationError):
        MotorConfig(nominal_rpm=nominal_rpm)


def test_amplitudes_are_nonnegative_while_phase_values_may_be_signed() -> None:
    """Signal amplitudes follow the spec while phase offsets remain signed."""
    phase = AxisValues(x=-0.5, y=0.0, z=0.5)
    assert phase.x == -0.5

    with pytest.raises(ValidationError):
        NonNegativeAxisValues(x=-0.1, y=0.0, z=0.0)


@pytest.mark.parametrize(
    "amplitude_field",
    ["rotational_peak_m_s2", "imbalance_peak_m_s2_at_intensity_1"],
)
def test_effective_config_rejects_negative_vibration_amplitudes(
    effective_config: dict[str, object], amplitude_field: str
) -> None:
    """Both baseline and imbalance acceleration peaks are non-negative."""
    invalid_config = effective_config.copy()
    signal_config = effective_config["signal"]
    assert isinstance(signal_config, dict)
    invalid_signal = signal_config.copy()
    invalid_signal[amplitude_field] = {"x": -0.1, "y": 0.0, "z": 0.0}
    invalid_config["signal"] = invalid_signal

    with pytest.raises(ValidationError):
        EffectiveRunConfig.model_validate(invalid_config)


def test_effective_config_allows_negative_phase_offsets(
    effective_config: dict[str, object],
) -> None:
    """Rotational phase offsets are finite angles and may be negative."""
    signed_phase_config = effective_config.copy()
    signal_config = effective_config["signal"]
    assert isinstance(signal_config, dict)
    signed_signal = signal_config.copy()
    signed_signal["rotational_phase_rad"] = {"x": -0.5, "y": 0.0, "z": 0.5}
    signed_phase_config["signal"] = signed_signal

    run_config = EffectiveRunConfig.model_validate(signed_phase_config)

    assert run_config.signal.rotational_phase_rad.x == -0.5


@pytest.mark.parametrize("identifier_field", ["asset_id", "device_id", "run_id"])
@pytest.mark.parametrize("blank_value", ["", " \t\n"])
def test_effective_config_rejects_blank_identifiers(
    effective_config: dict[str, object], identifier_field: str, blank_value: str
) -> None:
    """Identifier fields must contain at least one non-whitespace character."""
    invalid_config = effective_config.copy()
    invalid_config[identifier_field] = blank_value

    with pytest.raises(ValidationError):
        EffectiveRunConfig.model_validate(invalid_config)


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
def test_effective_config_rejects_noncanonical_entity_ulids(
    effective_config: dict[str, object],
    identifier_field: str,
    invalid_ulid: object,
) -> None:
    """Device and asset IDs must match the strict canonical ULID profile."""
    invalid_config = effective_config.copy()
    invalid_config[identifier_field] = invalid_ulid

    with pytest.raises(ValidationError):
        EffectiveRunConfig.model_validate(invalid_config)


@pytest.mark.parametrize(
    "sensor_groups",
    [
        ("vibration", "temperature"),
        ("vibration", "temperature", "temperature"),
        ("vibration", "temperature", "pressure"),
    ],
)
def test_motor_config_rejects_missing_duplicate_or_unsupported_groups(
    sensor_groups: tuple[str, ...],
) -> None:
    """Motor models reject groups outside the required v0.1 set."""
    with pytest.raises(ValidationError):
        MotorConfig(nominal_rpm=1800.0, sensor_groups=sensor_groups)  # type: ignore[arg-type]


def test_effective_run_config_exposes_motor_and_imbalance_models(
    effective_config: dict[str, object],
) -> None:
    """The existing serialized run config maps to typed domain models."""
    run_config = EffectiveRunConfig.model_validate(effective_config)

    assert run_config.motor.nominal_rpm == 1800.0
    assert run_config.motor.sensor_groups == REQUIRED_SENSOR_GROUPS
    assert isinstance(run_config.operating_condition, ImbalanceCondition)
    assert run_config.operating_condition.condition_intensity == 0.7
    applied_peak = run_config.operating_condition.applied_peak_m_s2
    assert applied_peak.x == pytest.approx(0.07)
    assert applied_peak.y == pytest.approx(0.035)
    assert applied_peak.z == pytest.approx(0.035)
    assert "motor" not in run_config.model_dump()
    assert "operating_condition" not in run_config.model_dump()


def test_effective_run_config_exposes_normal_condition(
    effective_config: dict[str, object],
) -> None:
    """Normal runs retain a zero-intensity condition with no added effect."""
    normal_config = effective_config.copy()
    normal_config["condition"] = "normal"
    normal_config["condition_intensity"] = 0.0

    run_config = EffectiveRunConfig.model_validate(normal_config)

    assert isinstance(run_config.operating_condition, NormalCondition)
    assert run_config.operating_condition.condition_intensity == 0.0


def test_effective_run_config_exposes_overheating_parameters(
    effective_config: dict[str, object],
) -> None:
    """Overheating intensity scales its configured full-run rise."""
    overheating_config = effective_config.copy()
    overheating_config["condition"] = "overheating"
    overheating_config["condition_intensity"] = 0.5

    run_config = EffectiveRunConfig.model_validate(overheating_config)

    assert isinstance(run_config.operating_condition, OverheatingCondition)
    assert run_config.operating_condition.temperature_rise_c_at_intensity_1 == 10.0
    assert run_config.operating_condition.applied_temperature_rise_c == 5.0


@pytest.mark.parametrize(
    ("condition", "condition_intensity"),
    [
        ("normal", 0.1),
        ("imbalance", 0.0),
        ("overheating", 1.1),
    ],
)
def test_effective_run_config_rejects_invalid_condition_intensity(
    effective_config: dict[str, object],
    condition: str,
    condition_intensity: float,
) -> None:
    """The flattened run config enforces condition-specific intensity rules."""
    invalid_config = effective_config.copy()
    invalid_config["condition"] = condition
    invalid_config["condition_intensity"] = condition_intensity

    with pytest.raises(ValidationError):
        EffectiveRunConfig.model_validate(invalid_config)
