#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

# Separate project/volumes and random host ports keep developer data untouched.
project="machinepulse-test-$(date +%s)-$$"
export MACHINEPULSE_MQTT_PORT=0
export MACHINEPULSE_KAFKA_PORT=0
compose=(docker compose --project-name "$project" --file infra/docker/compose.yaml)

cleanup() {
  result=$?
  trap - EXIT
  if [ "$result" -ne 0 ]; then
    "${compose[@]}" ps --all || true
    "${compose[@]}" logs --no-color --tail 100 || true
  fi
  # Only this run's disposable data is removed.
  "${compose[@]}" down --volumes --remove-orphans || true
  exit "$result"
}
trap cleanup EXIT

"${compose[@]}" config --quiet
"${compose[@]}" up --detach --wait --wait-timeout 180

topic=machinepulse-infra-smoke
payload=p02-002-persistent-message

# Register an offline MQTT 5 QoS 1 subscription with a 24-hour expiry.
"${compose[@]}" exec -T mqtt mosquitto_sub -V mqttv5 -c -x 86400 \
  -i p02-002-smoke -q 1 -t "$topic" -E -W 10
"${compose[@]}" exec -T mqtt mosquitto_pub -V mqttv5 -q 1 \
  -t "$topic" -m "$payload"

"${compose[@]}" exec -T kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka:19092 --create --topic "$topic" \
  --partitions 1 --replication-factor 1
printf '%s\n' "$payload" | "${compose[@]}" exec -T kafka \
  /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server kafka:19092 \
  --topic "$topic" --producer-property acks=all

# Recreate containers while retaining the volumes, exercising on-disk state.
"${compose[@]}" down
"${compose[@]}" up --detach --wait --wait-timeout 180

received=$("${compose[@]}" exec -T mqtt mosquitto_sub -V mqttv5 -c -x 86400 \
  -i p02-002-smoke -q 1 -t "$topic" -C 1 -W 10)
[ "$received" = "$payload" ]
echo "PASS: MQTT 5 offline QoS 1 session and queued message survive container recreation"

received=$("${compose[@]}" exec -T kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:19092 --topic "$topic" --from-beginning \
  --max-messages 1 --timeout-ms 15000)
[ "$received" = "$payload" ]
echo "PASS: Kafka topic and record survive container recreation"
