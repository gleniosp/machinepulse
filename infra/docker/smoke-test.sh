#!/usr/bin/env bash
# Host entry point: requires Bash and Docker, not host Python or Go.
# verify-smoke.py runs only in the simulator's locked Python runtime via the
# read-only mounts and explicit container interpreter configured below.
set -euo pipefail

cd "$(dirname "$0")/../.."

scratch=$(mktemp -d "${TMPDIR:-/tmp}/machinepulse-containers.XXXXXX")
export MACHINEPULSE_SMOKE_PROJECT="machinepulse-containers-$(date +%s)-$$"
export MACHINEPULSE_SMOKE_OUTPUT="$scratch/output"
export MACHINEPULSE_MQTT_PORT=0
export MACHINEPULSE_KAFKA_PORT=0
export MACHINEPULSE_UID="$(id -u)"
export MACHINEPULSE_GID="$(id -g)"
export COMPOSE_PROFILES=""
mkdir "$MACHINEPULSE_SMOKE_OUTPUT"

# Ignore the developer's dotenv file. Project names, image tags, output, and
# broker volumes belong to this invocation; the host ports are disposable.
compose=(docker compose --env-file /dev/null
  --project-name "$MACHINEPULSE_SMOKE_PROJECT"
  --file compose.yaml --file infra/docker/compose.test.yaml)

cleanup() {
  result=$?
  trap - EXIT
  cleanup_failed=0
  if [ "$result" -ne 0 ]; then
    "${compose[@]}" ps --all || true
    "${compose[@]}" logs --no-color --tail 100 || true
  fi
  "${compose[@]}" down --volumes --remove-orphans || cleanup_failed=1
  for component in gateway simulator; do
    image="machinepulse-$component:$MACHINEPULSE_SMOKE_PROJECT"
    if docker image inspect "$image" >/dev/null 2>&1; then
      docker image rm "$image" >/dev/null || cleanup_failed=1
    fi
  done
  # Only the directory created by mktemp above is removed.
  rm -rf -- "$scratch"
  if [ "$result" -eq 0 ]; then
    result=$cleanup_failed
  fi
  exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

wait_for_log() {
  local message=$1
  local minimum=${2:-1}
  local attempt logs count
  for ((attempt = 0; attempt < 30; attempt++)); do
    logs=$("${compose[@]}" logs --no-color --no-log-prefix gateway)
    count=$(grep -F -c -- "\"msg\":\"$message\"" <<< "$logs" || true)
    if [ "$count" -ge "$minimum" ]; then
      return 0
    fi
    sleep 1
  done
  echo "Timed out waiting for $message ($minimum occurrences)" >&2
  return 1
}

# This interpreter is Python 3.13 from the image's Pixi default environment.
# Validation code and the fixture are mounted for tests, never baked into images.
verify=("${compose[@]}" run --rm --no-deps -T
  --volume "$PWD/infra/docker/verify-smoke.py:/checks/verify.py:ro"
  --volume "$PWD/tools/simulator/tests/fixtures/telemetry.v1.json:/checks/fixture.json:ro"
  --volume "$scratch:/checks/evidence:ro"
  --entrypoint /app/.pixi/envs/default/bin/python
  simulator /checks/verify.py)

"${compose[@]}" --profile tools config --quiet
"${compose[@]}" build --no-cache gateway simulator

for output in first second; do
  "${compose[@]}" run --rm --no-deps -T simulator generate \
    --config /app/tools/simulator/examples/runs.v1.json \
    --output-dir "simulator-output/$output"
done
"${verify[@]}" datasets

"${compose[@]}" up --no-build --detach --wait --wait-timeout 180
wait_for_log mqtt_connected
topic=$("${verify[@]}" topic)
"${compose[@]}" exec -T mqtt mosquitto_pub -V mqttv5 -q 1 \
  -t "$topic" -s < tools/simulator/tests/fixtures/telemetry.v1.json
wait_for_log telemetry_unacknowledged
"${compose[@]}" logs --no-color --no-log-prefix gateway > "$scratch/initial.log"
"${verify[@]}" gateway initial

"${compose[@]}" restart gateway
wait_for_log telemetry_unacknowledged 2
"${compose[@]}" logs --no-color --no-log-prefix gateway > "$scratch/restart.log"
"${verify[@]}" gateway restart

# Recreate every runtime container while retaining this test's broker volumes.
"${compose[@]}" down
"${compose[@]}" up --no-build --detach --wait --wait-timeout 180
wait_for_log telemetry_unacknowledged
"${compose[@]}" logs --no-color --no-log-prefix gateway > "$scratch/recreate.log"
"${verify[@]}" gateway recreate
echo "PASS: container builds, datasets, MQTT reception, restart, and recreation"
