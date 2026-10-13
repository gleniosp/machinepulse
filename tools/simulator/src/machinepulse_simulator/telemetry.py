"""Build, validate, and serialize ``telemetry.v1`` simulator events."""

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from json import dumps
from math import isfinite
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BeforeValidator,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
    model_validator,
)

from machinepulse_simulator.context import iter_context_windows
from machinepulse_simulator.domain import SimulatorModel
from machinepulse_simulator.models import EffectiveRunConfig
from machinepulse_simulator.reproducibility import event_id_for_window
from machinepulse_simulator.units import MILLISECONDS_PER_SECOND
from machinepulse_simulator.vibration import iter_vibration_windows


def _finite_number(value: object) -> float:
    """Accept finite JSON numbers and normalize them to floats.

    Args:
        value: Value supplied for a numeric measurement.

    Returns:
        The finite numeric value as a float.

    Raises:
        ValueError: If the value is not a finite JSON number.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("must be a finite number")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError("must be a finite number") from exc
    if not isfinite(number):
        raise ValueError("must be a finite number")
    return number


type FiniteNumber = Annotated[float, BeforeValidator(_finite_number)]
type TelemetryIdentifier = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"\S"),
]


class TelemetrySampling(SimulatorModel):
    """Sampling metadata carried by a ``telemetry.v1`` window."""

    rate_hz: int = Field(gt=0)
    sample_count: int = Field(gt=0)
    window_duration_ms: int = Field(gt=0)

    @model_validator(mode="after")
    def require_consistent_duration(self) -> "TelemetrySampling":
        """Require count and duration to agree by less than one sample interval.

        Returns:
            This validated sampling record.

        Raises:
            ValueError: If the duration differs by at least one sample interval.
        """
        count_duration_product = self.sample_count * MILLISECONDS_PER_SECOND
        rate_duration_product = self.rate_hz * self.window_duration_ms
        if abs(count_duration_product - rate_duration_product) >= (
            MILLISECONDS_PER_SECOND
        ):
            raise ValueError(
                "sample_count and window_duration_ms must agree by less than "
                "one sample interval"
            )
        return self


class TelemetryVibration(SimulatorModel):
    """Three vibration axes in metres per second squared."""

    x: list[FiniteNumber]
    y: list[FiniteNumber]
    z: list[FiniteNumber]


class TelemetryMeasurements(SimulatorModel):
    """Scalar context and vibration samples for one telemetry window."""

    temperature_c: FiniteNumber
    rpm: FiniteNumber = Field(ge=0)
    vibration_m_s2: TelemetryVibration


class TelemetryWindow(SimulatorModel):
    """Validated device-neutral ``telemetry.v1`` event."""

    schema_version: Literal["telemetry.v1"]
    event_id: str
    device_id: TelemetryIdentifier
    asset_id: TelemetryIdentifier
    occurred_at: datetime = Field(strict=False)
    sequence: int = Field(ge=0)
    sampling: TelemetrySampling
    measurements: TelemetryMeasurements

    @field_validator("event_id")
    @classmethod
    def require_canonical_uuid(cls, value: str) -> str:
        """Require the lowercase, hyphenated UUID representation.

        Args:
            value: Event identifier from the payload.

        Returns:
            The canonical event identifier unchanged.

        Raises:
            ValueError: If the event identifier is not a canonical UUID.
        """
        try:
            canonical_value = str(UUID(value))
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("event_id must be a canonical UUID") from exc
        if canonical_value != value:
            raise ValueError("event_id must be a lowercase hyphenated UUID")
        return value

    @field_validator("occurred_at", mode="before")
    @classmethod
    def require_timestamp_input(cls, value: object) -> object:
        """Limit timestamp input to an ISO string or a datetime value.

        Args:
            value: Timestamp value supplied for the event.

        Returns:
            The input for Pydantic's datetime parser.

        Raises:
            ValueError: If the input is not a timestamp string or datetime.
        """
        if not isinstance(value, (str, datetime)):
            raise ValueError("occurred_at must be a timezone-aware timestamp")
        return value

    @field_validator("occurred_at")
    @classmethod
    def require_utc_timestamp(cls, value: datetime) -> datetime:
        """Require an explicit UTC offset and normalize to UTC.

        Args:
            value: Parsed event timestamp.

        Returns:
            The timestamp normalized to UTC.

        Raises:
            ValueError: If the timestamp is naive or has a non-zero UTC offset.
        """
        if value.utcoffset() is None:
            raise ValueError("occurred_at must include timezone information")
        if value.utcoffset() != timedelta(0):
            raise ValueError("occurred_at must use UTC")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def require_declared_sample_counts(self) -> "TelemetryWindow":
        """Require every vibration axis to match the declared sample count.

        Returns:
            This validated telemetry window.

        Raises:
            ValueError: If an axis contains the wrong number of samples.
        """
        axes = self.measurements.vibration_m_s2
        axis_counts = {name: len(getattr(axes, name)) for name in ("x", "y", "z")}
        if any(count != self.sampling.sample_count for count in axis_counts.values()):
            actual_counts = ", ".join(
                f"{axis}={count}" for axis, count in axis_counts.items()
            )
            raise ValueError(
                "each vibration axis must contain sampling.sample_count values "
                f"({actual_counts}; expected {self.sampling.sample_count})"
            )
        return self


class TelemetryValidationError(ValueError):
    """Raised when a telemetry payload does not satisfy ``telemetry.v1``."""


def _format_validation_error(error: ValidationError) -> str:
    """Format Pydantic errors with their payload paths.

    Args:
        error: Validation error raised while parsing a telemetry payload.

    Returns:
        Semicolon-separated field paths and validation messages.
    """
    details: list[str] = []
    for item in error.errors(include_url=False):
        path = ".".join(str(part) for part in item["loc"])
        details.append(f"{path or 'payload'}: {item['msg']}")
    return "; ".join(details)


def validate_telemetry(payload: object) -> TelemetryWindow:
    """Validate a Python payload as a ``telemetry.v1`` event.

    Args:
        payload: Mapping or telemetry model to validate.

    Returns:
        A validated telemetry window.

    Raises:
        TelemetryValidationError: If a field is missing or violates the contract.
    """
    if isinstance(payload, TelemetryWindow):
        payload = payload.model_dump(mode="python")
    try:
        return TelemetryWindow.model_validate(payload)
    except ValidationError as exc:
        details = _format_validation_error(exc)
        raise TelemetryValidationError(
            f"invalid telemetry.v1 payload: {details}"
        ) from exc


def serialize_telemetry(payload: object) -> str:
    """Validate and serialize a telemetry event as stable compact JSON.

    Args:
        payload: Python payload or validated telemetry model.

    Returns:
        Compact JSON with deterministic key ordering.

    Raises:
        TelemetryValidationError: If the payload violates the contract.
    """
    telemetry = validate_telemetry(payload)
    return dumps(
        telemetry.model_dump(mode="json"),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def iter_telemetry_windows(
    config: EffectiveRunConfig,
) -> Iterator[TelemetryWindow]:
    """Yield contract-validated events from the configured simulator run.

    Sequence numbers begin at zero for each simulated run, matching the event
    identity input used by :func:`event_id_for_window`.

    Args:
        config: Fully validated, resolved configuration for the run.

    Yields:
        One ``telemetry.v1`` event per vibration and context window.
    """
    vibration_windows = iter_vibration_windows(config)
    context_windows = iter_context_windows(config)
    for sequence, (vibration, context) in enumerate(
        zip(vibration_windows, context_windows, strict=True)
    ):
        if context.window_index != sequence:
            raise ValueError("context window index does not match sequence")
        occurred_at = config.run.start_time_utc + timedelta(
            milliseconds=sequence * config.sampling.window_duration_ms
        )
        yield TelemetryWindow(
            schema_version="telemetry.v1",
            event_id=event_id_for_window(config.device_id, config.run_id, sequence),
            device_id=config.device_id,
            asset_id=config.asset_id,
            occurred_at=occurred_at,
            sequence=sequence,
            sampling=TelemetrySampling(
                rate_hz=vibration.sampling.rate_hz,
                sample_count=vibration.sampling.sample_count,
                window_duration_ms=vibration.sampling.window_duration_ms,
            ),
            measurements=TelemetryMeasurements(
                temperature_c=context.temperature_c,
                rpm=context.rpm,
                vibration_m_s2=TelemetryVibration(
                    x=list(vibration.vibration_m_s2.x),
                    y=list(vibration.vibration_m_s2.y),
                    z=list(vibration.vibration_m_s2.z),
                ),
            ),
        )
