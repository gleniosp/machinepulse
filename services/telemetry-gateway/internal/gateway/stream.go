package gateway

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/segmentio/kafka-go"
)

const InternalTopic = "machinepulse.telemetry.v1"
const InternalVersion = "internal.telemetry.v1"

// InternalEvent preserves validated telemetry and indexes its original identity.
type InternalEvent struct {
	SchemaVersion     string          `json:"schema_version"`
	Source            Source          `json:"source"`
	GatewayReceivedAt time.Time       `json:"gateway_received_at"`
	Payload           json.RawMessage `json:"payload"`
}

type messageWriter interface {
	WriteMessages(context.Context, ...kafka.Message) error
}

// StreamPublisher owns a synchronous Kafka writer. Close it after gateway Run ends.
type StreamPublisher struct{ writer *kafka.Writer }

func NewStreamPublisher(address string, timeout time.Duration) *StreamPublisher {
	return &StreamPublisher{writer: &kafka.Writer{
		Addr: kafka.TCP(address), Topic: InternalTopic, Balancer: &kafka.Hash{},
		RequiredAcks: kafka.RequireAll, Async: false, MaxAttempts: 1,
		BatchSize: 1, ReadTimeout: timeout, WriteTimeout: timeout,
		AllowAutoTopicCreation: false,
	}}
}

func (p *StreamPublisher) Close() error { return p.writer.Close() }

// Publish returns success only after Kafka has acknowledged the record.
func (p *StreamPublisher) Publish(ctx context.Context, delivery Delivery) error {
	return publishEvent(ctx, p.writer, delivery)
}

func publishEvent(ctx context.Context, writer messageWriter, delivery Delivery) error {
	event := InternalEvent{InternalVersion, delivery.Source, delivery.GatewayReceivedAt.UTC(), delivery.Payload}
	value, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("encode internal telemetry: %w", err)
	}
	if err := writer.WriteMessages(ctx, kafka.Message{Key: []byte(delivery.Source.DeviceID), Value: value}); err != nil {
		return fmt.Errorf("publish internal telemetry: %w", err)
	}
	return ctx.Err()
}
