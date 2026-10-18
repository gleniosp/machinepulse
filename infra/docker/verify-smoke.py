"""Validate smoke-test evidence inside the simulator container.

The host Bash wrapper mounts this file, a fixture, and log snapshots at /checks
and invokes the image's locked Python 3.13 interpreter. Run the wrapper rather
than executing this helper on the host; its paths refer to container mounts.
Only the Python standard library is required. Local static checks use
the repository's pinned Pixi development tools without executing this module.
"""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys


def verify_datasets() -> None:
    """Verify repeatable container output, sidecar separation, and host ownership."""
    output = Path("/output/simulator-output")
    configs = json.loads(
        Path("/app/tools/simulator/examples/runs.v1.json").read_text()
    )["runs"]
    assert len(list((output / "first").glob("run-*"))) == len(configs)
    for number, config in enumerate(configs, start=1):
        first = output / "first" / f"run-{number:03d}"
        second = output / "second" / first.name
        for filename in ("manifest.json", "telemetry.jsonl", "ground-truth.jsonl"):
            assert (first / filename).read_bytes() == (second / filename).read_bytes()
            assert (first / filename).stat().st_uid == os.getuid()
        manifest = json.loads((first / "manifest.json").read_text())
        telemetry = [
            json.loads(line)
            for line in (first / "telemetry.jsonl").read_text().splitlines()
        ]
        sidecar = [
            json.loads(line)
            for line in (first / "ground-truth.jsonl").read_text().splitlines()
        ]
        assert len(telemetry) == len(sidecar) == config["run"]["window_count"]
        assert [event["event_id"] for event in telemetry] == [
            event["event_id"] for event in sidecar
        ]
        assert {event["condition"] for event in sidecar} == {config["condition"]}
        assert all("condition" not in event for event in telemetry)
        assert manifest["code_revision"] is None
        assert manifest["working_tree_dirty"] is None
    assert shutil.which("pixi") is None
    assert importlib.util.find_spec("pytest") is None
    assert not Path("/app/.git").exists()
    print(
        "PASS: repeatable datasets, separate labels, ownership, and runtime isolation"
    )


def verify_gateway(stage: str) -> None:
    """Check observed source identity and persistent-session recovery.

    Args:
        stage: Log snapshot name: initial, restart, or recreate.
    """
    records = [
        json.loads(line)
        for line in Path(f"/checks/evidence/{stage}.log").read_text().splitlines()
        if line.strip()
    ]
    fixture = json.loads(Path("/checks/fixture.json").read_text())
    received = [record for record in records if record["msg"] == "telemetry_received"]
    assert len(received) >= (2 if stage == "restart" else 1)
    for record in received:
        for field in ("event_id", "device_id", "asset_id", "occurred_at"):
            assert record[field] == fixture[field], (stage, field, record)
        assert record["gateway_received_at"].endswith("Z")
    assert any(record["msg"] == "telemetry_unacknowledged" for record in records)
    if stage == "initial":
        assert any(record["msg"] == "mqtt_subscribed" for record in records)
    else:
        assert any(
            record["msg"] == "mqtt_connected" and record["session_present"]
            for record in records
        )
    print(f"PASS: gateway {stage}, source identity preserved and disposition pending")


if __name__ == "__main__":
    match sys.argv[1:]:
        case ["datasets"]:
            verify_datasets()
        case ["topic"]:
            fixture = json.loads(Path("/checks/fixture.json").read_text())
            print(f"machinepulse/v1/telemetry/{fixture['device_id']}")
        case ["gateway", stage] if stage in {"initial", "restart", "recreate"}:
            verify_gateway(stage)
        case _:
            raise SystemExit("expected datasets, topic, or gateway <stage>")
