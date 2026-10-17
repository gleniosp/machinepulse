package gateway

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"time"
)

// Source indexes producer metadata without parsing or normalizing event time.
// Contract validation and invalid-message disposition belong to P02-004.
type Source struct {
	EventID       string `json:"event_id"`
	DeviceID      string `json:"device_id"`
	AssetID       string `json:"asset_id"`
	OccurredAt    string `json:"occurred_at"`
	SchemaVersion string `json:"schema_version"`
}

// Delivery is an in-process handoff, not the internal event envelope (P02-005).
// Payload is an owned, unchanged copy of the MQTT payload.
type Delivery struct {
	Source            Source
	Payload           json.RawMessage
	Topic             string
	GatewayReceivedAt time.Time
}

func decode(topic string, payload []byte, receivedAt time.Time) (Delivery, error) {
	var fields map[string]json.RawMessage
	decoder := json.NewDecoder(bytes.NewReader(payload))
	if err := decoder.Decode(&fields); err != nil {
		return Delivery{}, fmt.Errorf("decode telemetry object: %w", err)
	}
	if fields == nil {
		return Delivery{}, errors.New("telemetry must be a JSON object")
	}
	if err := decoder.Decode(new(any)); err != io.EOF {
		return Delivery{}, errors.New("telemetry must contain exactly one JSON object")
	}
	var source Source
	if err := json.Unmarshal(payload, &source); err != nil {
		return Delivery{}, fmt.Errorf("decode producer metadata: %w", err)
	}
	return Delivery{
		Source: source, Payload: append(json.RawMessage(nil), payload...),
		Topic: topic, GatewayReceivedAt: receivedAt.UTC(),
	}, nil
}
