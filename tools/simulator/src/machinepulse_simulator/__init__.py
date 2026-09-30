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

__all__ = [
    "GENERATOR_VERSION",
    "ImbalanceCondition",
    "MANIFEST_VERSION",
    "MotorConfig",
    "NormalCondition",
    "OverheatingCondition",
    "REQUIRED_SENSOR_GROUPS",
    "TELEMETRY_NAMESPACE",
    "create_ground_truth_record",
    "create_run_manifest",
    "event_id_for_window",
    "serialize_json",
]
