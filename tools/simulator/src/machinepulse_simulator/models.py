"""Validated models for simulator configuration and reproducibility records."""

from datetime import datetime, timedelta
from typing import Annotated, Literal
from pydantic import (
    UUID5,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from machinepulse_simulator.domain import (
    AxisValues,
    ConditionName,
    ImbalanceCondition,
    MotorConfig,
    NormalCondition,
    OperatingCondition,
    OverheatingCondition,
    NonNegativeAxisValues,
    SimulatorModel,
)
from machinepulse_simulator.units import MILLISECONDS_PER_SECOND


type NonBlankString = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"\S"),
]


class SamplingConfig(SimulatorModel):
    """Sampling rate and window duration for vibration channels."""

    rate_hz: int = Field(gt=0)
    window_duration_ms: int = Field(gt=0)

    @property
    def sample_count(self) -> int:
        """Return the number of samples represented by one configured window.

        Returns:
            The integral samples per axis for this sampling configuration.
        """
        return self.rate_hz * self.window_duration_ms // MILLISECONDS_PER_SECOND

    @model_validator(mode="after")
    def require_integral_sample_count(self) -> "SamplingConfig":
        """Reject windows that do not contain an integral number of samples.

        Returns:
            This validated sampling configuration.

        Raises:
            ValueError: If the rate and duration imply a fractional sample.
        """
        sample_count_numerator = self.rate_hz * self.window_duration_ms
        if sample_count_numerator % MILLISECONDS_PER_SECOND != 0:
            raise ValueError(
                "sampling rate and window duration must produce an "
                "integral sample count"
            )
        return self


class RunConfig(SimulatorModel):
    """Run-wide controls required to reproduce generated events."""

    window_count: int = Field(gt=0)
    seed: int = Field(ge=0)
    start_time_utc: datetime = Field(strict=False)
    execution_mode: Literal["accelerated", "real_time"]

    @field_validator("start_time_utc")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        """Reject naive or non-UTC timestamps.

        Args:
            value: Parsed run start timestamp.

        Returns:
            The UTC timestamp unchanged.

        Raises:
            ValueError: If the timestamp is naive or uses a non-UTC offset.
        """
        if value.utcoffset() != timedelta(0):
            raise ValueError("start_time_utc must use UTC")
        return value


class SignalConfig(SimulatorModel):
    """Configurable baseline and condition-specific signal parameters."""

    rotational_peak_m_s2: NonNegativeAxisValues
    rotational_phase_rad: AxisValues
    noise_std_m_s2: float = Field(ge=0, allow_inf_nan=False)
    imbalance_peak_m_s2_at_intensity_1: NonNegativeAxisValues


class TemperatureConfig(SimulatorModel):
    """Synthetic temperature context parameters."""

    initial_c: float = Field(allow_inf_nan=False)
    overheating_rise_c_at_intensity_1: float = Field(ge=0, allow_inf_nan=False)


class EffectiveRunConfig(SimulatorModel):
    """Complete, validated simulator configuration for one run."""

    asset_id: NonBlankString
    device_id: NonBlankString
    run_id: NonBlankString
    nominal_rpm: float = Field(gt=0, allow_inf_nan=False)
    condition: ConditionName
    condition_intensity: float = Field(ge=0, le=1, allow_inf_nan=False)
    sampling: SamplingConfig
    run: RunConfig
    signal: SignalConfig
    temperature: TemperatureConfig

    @property
    def motor(self) -> MotorConfig:
        """Return the domain model for this run's motor and required sensors.

        Returns:
            The validated motor model, including the v0.1 sensor groups.
        """
        return MotorConfig(nominal_rpm=self.nominal_rpm)

    @property
    def operating_condition(self) -> OperatingCondition:
        """Return the condition-specific model derived from this run config.

        Returns:
            The validated domain model for the selected operating condition.
        """
        if self.condition == "normal":
            return NormalCondition(condition_intensity=self.condition_intensity)
        if self.condition == "imbalance":
            return ImbalanceCondition(
                condition_intensity=self.condition_intensity,
                peak_m_s2_at_intensity_1=(
                    self.signal.imbalance_peak_m_s2_at_intensity_1
                ),
            )
        return OverheatingCondition(
            condition_intensity=self.condition_intensity,
            temperature_rise_c_at_intensity_1=(
                self.temperature.overheating_rise_c_at_intensity_1
            ),
        )

    @model_validator(mode="after")
    def validate_condition_intensity(self) -> "EffectiveRunConfig":
        """Require condition intensity to agree with the selected scenario.

        Returns:
            This validated configuration.

        Raises:
            ValueError: If normal/fault intensity rules are violated.
        """
        if self.condition == "normal" and self.condition_intensity != 0:
            raise ValueError("normal condition requires zero intensity")
        if self.condition != "normal" and self.condition_intensity == 0:
            raise ValueError("fault condition requires positive intensity")
        return self


class RunManifest(SimulatorModel):
    """Versioned provenance and effective configuration for a run."""

    manifest_version: Literal["machinepulse.run-manifest.v1"]
    run_id: NonBlankString
    generator_version: NonBlankString
    code_revision: NonBlankString | None
    working_tree_dirty: bool | None
    effective_config: EffectiveRunConfig

    @model_validator(mode="after")
    def match_effective_run_id(self) -> "RunManifest":
        """Keep the manifest identity aligned with its effective config.

        Returns:
            This validated manifest.

        Raises:
            ValueError: If the manifest and effective config have different IDs.
        """
        if self.run_id != self.effective_config.run_id:
            raise ValueError("run_id must match effective_config.run_id")
        return self


class GroundTruthRecord(SimulatorModel):
    """Condition label and reproduction metadata for one telemetry event."""

    event_id: UUID5
    run_id: NonBlankString
    condition: ConditionName
    condition_intensity: float = Field(ge=0, le=1, allow_inf_nan=False)
    seed: int = Field(ge=0)
    generator_version: NonBlankString
    code_revision: NonBlankString | None
    working_tree_dirty: bool | None
    effective_config: EffectiveRunConfig

    @model_validator(mode="after")
    def match_effective_config(self) -> "GroundTruthRecord":
        """Keep duplicated sidecar values aligned with the effective config.

        Returns:
            This validated ground-truth record.

        Raises:
            ValueError: If a duplicated value differs from the run config.
        """
        config = self.effective_config
        if self.run_id != config.run_id:
            raise ValueError("run_id must match effective_config.run_id")
        if self.condition != config.condition:
            raise ValueError("condition must match effective_config.condition")
        if self.condition_intensity != config.condition_intensity:
            raise ValueError(
                "condition_intensity must match effective_config.condition_intensity"
            )
        if self.seed != config.run.seed:
            raise ValueError("seed must match effective_config.run.seed")
        return self
