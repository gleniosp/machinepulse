import os
import subprocess
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest

from machinepulse_simulator import (
    create_ground_truth_record,
    create_run_manifest,
    event_id_for_window,
    serialize_json,
)
from machinepulse_simulator.reproducibility import (
    GENERATOR_VERSION,
    MANIFEST_VERSION,
    ReproducibilityError,
    resolve_source_revision,
)


def test_event_id_matches_stable_uuidv5_fixture() -> None:
    """Keep UUIDv5 output stable against its golden vector."""
    assert (
        event_id_for_window("simulator-0001", "run-0001", 0)
        == "52b0000c-29e7-59c3-8695-9aad56cd00ef"
    )


def test_event_id_encodes_unicode_tuple_without_ambiguity() -> None:
    """Keep tuple components distinct, including non-ASCII identifiers."""
    assert event_id_for_window("設備", "run:one", 1) != event_id_for_window(
        "設備:run", "one", 1
    )


def test_ground_truth_record_rejects_non_v5_event_id(
    effective_config: dict[str, object],
) -> None:
    """Reject otherwise valid UUIDs that do not follow the simulator's UUIDv5 rule.

    Args:
        effective_config: Shared resolved simulator configuration fixture.
    """
    manifest = create_run_manifest(
        effective_config, code_revision=None, working_tree_dirty=None
    )
    with pytest.raises(ReproducibilityError):
        create_ground_truth_record(str(uuid4()), manifest)
    assert event_id_for_window("設備", "run-0001", 0) == event_id_for_window(
        "設備", "run-0001", 0
    )


@pytest.mark.parametrize(
    ("device_id", "run_id", "sequence"),
    [("", "run", 0), ("device", " ", 0), ("device", "run", -1), ("d", "r", True)],
)
def test_event_id_rejects_invalid_identity(
    device_id: str, run_id: str, sequence: int
) -> None:
    """Reject invalid device, run, or sequence identity values.

    Args:
        device_id: Parameterized producer identifier.
        run_id: Parameterized run identifier.
        sequence: Parameterized device-local sequence.
    """
    with pytest.raises(ReproducibilityError):
        event_id_for_window(device_id, run_id, sequence)


def test_manifest_and_sidecar_match_golden_fixtures(
    effective_config: dict[str, object],
    run_manifest_json: str,
    ground_truth_json: str,
) -> None:
    """Match manifest and sidecar serialization to golden JSON files.

    Args:
        effective_config: Shared resolved simulator configuration fixture.
        run_manifest_json: Expected canonical manifest JSON.
        ground_truth_json: Expected canonical sidecar JSON.
    """
    manifest = create_run_manifest(
        effective_config, code_revision=None, working_tree_dirty=None
    )
    sidecar = create_ground_truth_record(
        event_id_for_window("simulator-0001", "run-0001", 0), manifest
    )

    assert serialize_json(manifest) == run_manifest_json
    assert serialize_json(sidecar) == ground_truth_json


def test_manifest_serialization_is_stable_and_separate_from_telemetry(
    effective_config: dict[str, object],
) -> None:
    """Ensure identical metadata serializes identically without leaking labels.

    Args:
        effective_config: Shared resolved simulator configuration fixture.
    """
    config = effective_config
    manifest = create_run_manifest(
        config,
        code_revision="abc123",
        working_tree_dirty=False,
    )
    repeated_manifest = create_run_manifest(
        effective_config,
        code_revision="abc123",
        working_tree_dirty=False,
    )
    assert serialize_json(manifest) == serialize_json(repeated_manifest)
    assert manifest["manifest_version"] == MANIFEST_VERSION
    assert manifest["generator_version"] == GENERATOR_VERSION
    assert "condition" not in manifest


def test_metadata_rejects_missing_seed_and_non_finite_values(
    effective_config: dict[str, object],
) -> None:
    """Reject invalid seed, timestamp, intensity, and non-finite config values.

    Args:
        effective_config: Shared resolved simulator configuration fixture.
    """
    invalid_config = effective_config.copy()
    invalid_config["run"] = {"seed": -1}
    with pytest.raises(ReproducibilityError, match="seed"):
        create_run_manifest(invalid_config, code_revision=None, working_tree_dirty=None)

    invalid_config = effective_config.copy()
    invalid_config["nominal_rpm"] = float("nan")
    with pytest.raises(ReproducibilityError, match="finite"):
        create_run_manifest(invalid_config, code_revision=None, working_tree_dirty=None)

    invalid_config = effective_config.copy()
    invalid_config["run"] = {"seed": 1234}
    with pytest.raises(ReproducibilityError, match="start_time_utc"):
        create_run_manifest(invalid_config, code_revision=None, working_tree_dirty=None)

    invalid_config = effective_config.copy()
    invalid_config["condition_intensity"] = 1.1
    with pytest.raises(ReproducibilityError, match="condition_intensity"):
        create_run_manifest(invalid_config, code_revision=None, working_tree_dirty=None)


def test_resolve_source_revision_uses_build_metadata_environment() -> None:
    """Use build-provided source revision metadata when available."""
    completed = subprocess.CompletedProcess(
        args=["git", "status"], returncode=0, stdout="", stderr=""
    )
    with (
        patch.dict(os.environ, {"MACHINEPULSE_CODE_REVISION": "build-rev-001"}),
        patch(
            "machinepulse_simulator.reproducibility.subprocess.run",
            return_value=completed,
        ) as run,
    ):
        assert resolve_source_revision(Path("/checkout")) == ("build-rev-001", False)

    assert run.call_count == 1


def test_resolve_source_revision_marks_unavailable_metadata_unknown() -> None:
    """Return unknown revision state when Git is unavailable."""
    with patch(
        "machinepulse_simulator.reproducibility.subprocess.run",
        side_effect=FileNotFoundError,
    ):
        assert resolve_source_revision(Path("/not-a-checkout")) == (None, None)


def test_resolve_source_revision_reads_git_revision_and_dirty_state() -> None:
    """Read the full Git revision and detect untracked working-tree files."""
    outputs = [
        subprocess.CompletedProcess(
            args=["git", "rev-parse"], returncode=0, stdout="full-revision\n", stderr=""
        ),
        subprocess.CompletedProcess(
            args=["git", "status"], returncode=0, stdout="?? untracked.txt\n", stderr=""
        ),
    ]
    with (
        patch.dict(os.environ, {"MACHINEPULSE_CODE_REVISION": ""}),
        patch(
            "machinepulse_simulator.reproducibility.subprocess.run",
            side_effect=outputs,
        ) as run,
    ):
        assert resolve_source_revision(Path("/checkout")) == (
            "full-revision",
            True,
        )
    assert run.call_count == 2


"""Tests for simulator run metadata and deterministic event identities."""
