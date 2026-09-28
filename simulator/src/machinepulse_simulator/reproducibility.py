"""Stable identity and metadata helpers for simulator runs."""

import json
import os
import subprocess
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ValidationError

from .models import EffectiveRunConfig, GroundTruthRecord, RunManifest

GENERATOR_VERSION = "simulator.v1"
MANIFEST_VERSION: Literal["machinepulse.run-manifest.v1"] = (
    "machinepulse.run-manifest.v1"
)
TELEMETRY_NAMESPACE = uuid.UUID("137bfca0-3f75-56ce-a36c-932f0bc60c36")


class ReproducibilityError(ValueError):
    """Raised when reproducibility metadata is invalid or incomplete."""


def _required_text(value: object, field: str) -> str:
    """Validate and return a non-blank string.

    Args:
        value: Value to validate.
        field: Field name used in the validation error.

    Returns:
        The original string value.

    Raises:
        ReproducibilityError: If value is not a non-blank string.
    """
    if not isinstance(value, str) or not value.strip():
        raise ReproducibilityError(f"{field} must be a non-empty string")
    return value


def event_id_for_window(device_id: str, run_id: str, sequence: int) -> str:
    """Create a stable UUIDv5 for one simulator telemetry window.

    Args:
        device_id: Non-empty producer identifier.
        run_id: Non-empty generated-run identifier.
        sequence: Non-negative device-local window sequence.

    Returns:
        Canonical lowercase, hyphenated UUID string.

    Raises:
        ReproducibilityError: If an identity value is invalid.
    """
    device_id = _required_text(device_id, "device_id")
    run_id = _required_text(run_id, "run_id")
    if type(sequence) is not int or sequence < 0:
        raise ReproducibilityError("sequence must be a non-negative integer")

    name = json.dumps(
        [device_id, run_id, sequence],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return str(uuid.uuid5(TELEMETRY_NAMESPACE, name))


def serialize_json(value: object) -> str:
    """Serialize metadata as compact, deterministically ordered JSON.

    Args:
        value: JSON-compatible value to serialize.

    Returns:
        UTF-8-compatible JSON text with sorted object keys.

    Raises:
        ReproducibilityError: If value cannot be represented as finite JSON.
    """
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ReproducibilityError(f"metadata is not valid JSON: {exc}") from exc


def create_run_manifest(
    effective_config: Mapping[str, object],
    *,
    code_revision: str | None,
    working_tree_dirty: bool | None,
    generator_version: str = GENERATOR_VERSION,
) -> dict[str, object]:
    """Build the versioned manifest for a resolved simulator run.

    Args:
        effective_config: Complete configuration, including resolved start time.
        code_revision: Source-control revision, or None if unavailable.
        working_tree_dirty: Git dirty state, or None if unknown.
        generator_version: Stable identifier for simulator output behavior.

    Returns:
        JSON-compatible run manifest.

    Raises:
        ReproducibilityError: If metadata or configuration fields are invalid.
    """
    try:
        config = EffectiveRunConfig.model_validate(effective_config)
        manifest = RunManifest(
            manifest_version=MANIFEST_VERSION,
            run_id=config.run_id,
            generator_version=generator_version,
            code_revision=code_revision,
            working_tree_dirty=working_tree_dirty,
            effective_config=config,
        )
    except ValidationError as exc:
        raise ReproducibilityError(f"invalid effective configuration: {exc}") from exc
    return manifest.model_dump(mode="json")


def create_ground_truth_record(
    event_id: str, manifest: Mapping[str, object]
) -> dict[str, object]:
    """Create ground-truth metadata associated with a telemetry event.

    Args:
        event_id: Canonical UUID for the telemetry window.
        manifest: Run manifest containing configuration and provenance.

    Returns:
        JSON-compatible sidecar record for the event.

    Raises:
        ReproducibilityError: If the event ID or manifest is invalid.
    """
    try:
        parsed_event_id = UUID(event_id)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ReproducibilityError("event_id must be a canonical UUID") from exc
    if str(parsed_event_id) != event_id:
        raise ReproducibilityError("event_id must be a canonical lowercase UUID")
    try:
        validated_manifest = RunManifest.model_validate(manifest)
        if validated_manifest.run_id != validated_manifest.effective_config.run_id:
            raise ReproducibilityError(
                "manifest run_id does not match effective_config"
            )
        record = GroundTruthRecord(
            event_id=parsed_event_id,
            run_id=validated_manifest.run_id,
            condition=validated_manifest.effective_config.condition,
            condition_intensity=validated_manifest.effective_config.condition_intensity,
            seed=validated_manifest.effective_config.run.seed,
            generator_version=validated_manifest.generator_version,
            code_revision=validated_manifest.code_revision,
            working_tree_dirty=validated_manifest.working_tree_dirty,
            effective_config=validated_manifest.effective_config,
        )
    except ValidationError as exc:
        raise ReproducibilityError(f"invalid run manifest: {exc}") from exc
    return record.model_dump(mode="json")


def resolve_source_revision(
    repository: Path | None = None,
) -> tuple[str | None, bool | None]:
    """Find the source revision and dirty state for the current run.

    Checks Git metadata first, with an environment override for packaged builds.

    Args:
        repository: Git working directory to inspect, or None to use the current
            working directory.

    Returns:
        A pair of source revision and dirty state; either can be None when
        unavailable.
    """
    cwd = repository
    revision = os.environ.get("MACHINEPULSE_CODE_REVISION", "").strip() or None
    try:
        if revision is None:
            completed = subprocess.run(
                ["git", "rev-parse", "--verify", "HEAD"],
                check=True,
                capture_output=True,
                cwd=cwd,
                text=True,
            )
            revision = completed.stdout.strip() or None

        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            check=True,
            capture_output=True,
            cwd=cwd,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return revision, None

    return revision, bool(status.stdout.strip())
