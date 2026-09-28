"""Validated models for simulator configuration and reproducibility records."""

from datetime import datetime, timedelta
from typing import Literal
from pydantic import (
    UUID5,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class SimulatorModel(BaseModel):
    """Base model that rejects undeclared fields and implicit coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class AxisValues(SimulatorModel):
    """Finite per-axis numeric values."""

    x: float = Field(allow_inf_nan=False)
    y: float = Field(allow_inf_nan=False)
    z: float = Field(allow_inf_nan=False)


class SamplingConfig(SimulatorModel):
    """Sampling rate and window duration for vibration channels."""

    rate_hz: int = Field(gt=0)
    window_duration_ms: int = Field(gt=0)


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

    rotational_peak_m_s2: AxisValues
    rotational_phase_rad: AxisValues
    noise_std_m_s2: float = Field(ge=0, allow_inf_nan=False)
    imbalance_peak_m_s2_at_intensity_1: AxisValues


class TemperatureConfig(SimulatorModel):
    """Synthetic temperature context parameters."""

    initial_c: float = Field(allow_inf_nan=False)
    overheating_rise_c_at_intensity_1: float = Field(ge=0, allow_inf_nan=False)


class EffectiveRunConfig(SimulatorModel):
    """Complete, validated simulator configuration for one run."""

    asset_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    nominal_rpm: float = Field(gt=0, allow_inf_nan=False)
    condition: Literal["normal", "imbalance", "overheating"]
    condition_intensity: float = Field(ge=0, le=1, allow_inf_nan=False)
    sampling: SamplingConfig
    run: RunConfig
    signal: SignalConfig
    temperature: TemperatureConfig

    @field_validator("asset_id", "device_id", "run_id")
    @classmethod
    def require_non_blank_identifier(cls, value: str) -> str:
        """Reject identifiers that contain only whitespace.

        Args:
            value: Identifier to validate.

        Returns:
            The original identifier.

        Raises:
            ValueError: If the identifier is blank.
        """
        if not value.strip():
            raise ValueError("identifier must not be blank")
        return value

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
    run_id: str = Field(min_length=1)
    generator_version: str = Field(min_length=1)
    code_revision: str | None = Field(min_length=1)
    working_tree_dirty: bool | None
    effective_config: EffectiveRunConfig


class GroundTruthRecord(SimulatorModel):
    """Condition label and reproduction metadata for one telemetry event."""

    event_id: UUID5
    run_id: str
    condition: Literal["normal", "imbalance", "overheating"]
    condition_intensity: float
    seed: int
    generator_version: str
    code_revision: str | None
    working_tree_dirty: bool | None
    effective_config: EffectiveRunConfig
