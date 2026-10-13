"""MachinePulse synthetic telemetry simulator."""

from .domain import (
    REQUIRED_SENSOR_GROUPS,
    ImbalanceCondition,
    MotorConfig,
    NormalCondition,
    OverheatingCondition,
)
from .reproducibility import (
    GENERATOR_VERSION,
    MANIFEST_VERSION,
    TELEMETRY_NAMESPACE,
    create_ground_truth_record,
    create_run_manifest,
    event_id_for_window,
    serialize_json,
)
from .telemetry import (
    TelemetryValidationError,
    TelemetryWindow,
    iter_telemetry_windows,
    serialize_telemetry,
    validate_telemetry,
)

__all__ = [
    "GENERATOR_VERSION",
    "ImbalanceCondition",
    "MANIFEST_VERSION",
    "MotorConfig",
    "NormalCondition",
    "OverheatingCondition",
    "REQUIRED_SENSOR_GROUPS",
    "TELEMETRY_NAMESPACE",
    "TelemetryValidationError",
    "TelemetryWindow",
    "create_ground_truth_record",
    "create_run_manifest",
    "event_id_for_window",
    "iter_telemetry_windows",
    "serialize_telemetry",
    "serialize_json",
    "validate_telemetry",
]
