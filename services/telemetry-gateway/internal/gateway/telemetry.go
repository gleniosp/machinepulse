package gateway

import (
	"encoding/json"
	"time"
)

// Source indexes untrusted producer strings without normalizing event time.
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

func deliveryFor(topic string, payload []byte, receivedAt time.Time) Delivery {
	delivery := Delivery{
		Payload: append(json.RawMessage(nil), payload...),
		Topic:   topic, GatewayReceivedAt: receivedAt.UTC(),
	}
	var fields map[string]json.RawMessage
	// Failure of one metadata field must not discard other recoverable fields.
	if json.Unmarshal(payload, &fields) == nil {
		for key, target := range map[string]*string{
			"event_id": &delivery.Source.EventID, "device_id": &delivery.Source.DeviceID,
			"asset_id": &delivery.Source.AssetID, "occurred_at": &delivery.Source.OccurredAt,
			"schema_version": &delivery.Source.SchemaVersion,
		} {
			_ = json.Unmarshal(fields[key], target)
		}
	}
	return delivery
}
