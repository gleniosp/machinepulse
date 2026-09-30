"""Domain models for motors and synthetic operating conditions."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


type SensorGroup = Literal["vibration", "temperature", "rpm"]
type ConditionName = Literal["normal", "imbalance", "overheating"]
REQUIRED_SENSOR_GROUPS: tuple[SensorGroup, SensorGroup, SensorGroup] = (
    "vibration",
    "temperature",
    "rpm",
)


class SimulatorModel(BaseModel):
    """Base model that rejects undeclared fields and implicit coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class AxisValues(SimulatorModel):
    """Finite signed per-axis values, such as vibration phase offsets."""

    x: float = Field(allow_inf_nan=False)
    y: float = Field(allow_inf_nan=False)
    z: float = Field(allow_inf_nan=False)


class NonNegativeAxisValues(AxisValues):
    """Finite non-negative per-axis amplitudes."""

    x: float = Field(ge=0, allow_inf_nan=False)
    y: float = Field(ge=0, allow_inf_nan=False)
    z: float = Field(ge=0, allow_inf_nan=False)


class MotorConfig(SimulatorModel):
    """Motor operating point and required v0.1 measurement groups."""

    nominal_rpm: float = Field(gt=0, allow_inf_nan=False)
    sensor_groups: tuple[SensorGroup, SensorGroup, SensorGroup] = REQUIRED_SENSOR_GROUPS

    @model_validator(mode="after")
    def require_v01_sensor_groups(self) -> "MotorConfig":
        """Require the three measurement groups defined by the v0.1 contract.

        Returns:
            This validated motor configuration.

        Raises:
            ValueError: If a required sensor group is missing or duplicated.
        """
        if set(self.sensor_groups) != set(REQUIRED_SENSOR_GROUPS):
            raise ValueError(
                "sensor_groups must include vibration, temperature, and rpm once"
            )
        return self


class NormalCondition(SimulatorModel):
    """Baseline condition with no condition-specific effect."""

    condition: Literal["normal"] = "normal"
    condition_intensity: float = Field(
        default=0.0,
        ge=0.0,
        le=0.0,
        allow_inf_nan=False,
    )


class ImbalanceCondition(SimulatorModel):
    """Imbalance effect scaled from peaks configured at intensity 1.0.

    The intensity-1 values are the per-axis peak amplitudes when
    ``condition_intensity`` is 1.0. Lower intensities scale those peaks
    linearly.
    """

    condition: Literal["imbalance"] = "imbalance"
    condition_intensity: float = Field(gt=0, le=1, allow_inf_nan=False)
    peak_m_s2_at_intensity_1: NonNegativeAxisValues

    @property
    def applied_peak_m_s2(self) -> NonNegativeAxisValues:
        """Return the configured per-axis peaks scaled by condition intensity.

        Returns:
            The applied synthetic acceleration peak for each axis.
        """
        return NonNegativeAxisValues(
            x=self.peak_m_s2_at_intensity_1.x * self.condition_intensity,
            y=self.peak_m_s2_at_intensity_1.y * self.condition_intensity,
            z=self.peak_m_s2_at_intensity_1.z * self.condition_intensity,
        )


class OverheatingCondition(SimulatorModel):
    """Temperature rise scaled from its configured value at intensity 1.0.

    The configured value is the total rise at ``condition_intensity`` 1.0.
    Lower intensities scale the rise linearly.
    """

    condition: Literal["overheating"] = "overheating"
    condition_intensity: float = Field(gt=0, le=1, allow_inf_nan=False)
    temperature_rise_c_at_intensity_1: float = Field(ge=0, allow_inf_nan=False)

    @property
    def applied_temperature_rise_c(self) -> float:
        """Return the run's total synthetic temperature rise in degrees Celsius.

        Returns:
            The intensity-scaled temperature rise.
        """
        return self.temperature_rise_c_at_intensity_1 * self.condition_intensity


type OperatingCondition = NormalCondition | ImbalanceCondition | OverheatingCondition
