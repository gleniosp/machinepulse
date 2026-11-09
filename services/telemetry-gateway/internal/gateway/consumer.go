package gateway

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"github.com/segmentio/kafka-go"
)

const DeadLetterTopic = "machinepulse.telemetry.dead-letter.v1"

// ConsumerReader must fetch without committing; commits must be synchronous.
// A reader belongs exclusively to one serial RunConsumer loop.
type ConsumerReader interface {
	FetchMessage(context.Context) (kafka.Message, error)
	CommitMessages(context.Context, ...kafka.Message) error
}

// ConsumerPolicy bounds processing per delivery. Terminal is stop or dead-letter.
type ConsumerPolicy struct {
	MaxAttempts      int
	Backoff          time.Duration
	OperationTimeout time.Duration
	Terminal         string
}

// DeadLetter retains exact source bytes and transport coordinates for replay.
type DeadLetter struct {
	SchemaVersion string    `json:"schema_version"`
	Topic         string    `json:"topic"`
	Partition     int       `json:"partition"`
	Offset        int64     `json:"offset"`
	Key           []byte    `json:"key"`
	Value         []byte    `json:"value"`
	Group         string    `json:"consumer_group"`
	Attempts      int       `json:"attempts"`
	Reason        string    `json:"failure_reason"`
	FailedAt      time.Time `json:"failed_at"`
}

// NewConsumerReader starts a group at the earliest retained record and disables
// auto commits. The caller closes it after RunConsumer returns.
func NewConsumerReader(address, group string) *kafka.Reader {
	return kafka.NewReader(kafka.ReaderConfig{Brokers: []string{address}, Topic: InternalTopic, GroupID: group, CommitInterval: 0, StartOffset: kafka.FirstOffset, MaxBytes: 2 * 1024 * 1024})
}

// NewDeadLetterWriter requires broker acknowledgement and explicit provisioning.
func NewDeadLetterWriter(address string, timeout time.Duration) *kafka.Writer {
	return &kafka.Writer{Addr: kafka.TCP(address), Topic: DeadLetterTopic, RequiredAcks: kafka.RequireAll, MaxAttempts: 1, BatchSize: 1, ReadTimeout: timeout, WriteTimeout: timeout}
}

func decodeConsumerEvent(m kafka.Message) (InternalEvent, error) {
	var event InternalEvent
	if err := json.Unmarshal(m.Value, &event); err != nil {
		return event, fmt.Errorf("decode envelope: %w", err)
	}
	var source Source
	if err := json.Unmarshal(event.Payload, &source); err != nil {
		return event, fmt.Errorf("decode source: %w", err)
	}
	if event.SchemaVersion != InternalVersion || event.Source.EventID == "" || event.Source.DeviceID == "" || event.Source.AssetID == "" || event.Source.OccurredAt == "" || event.Source.SchemaVersion != "telemetry.v1" || event.Source != source || event.GatewayReceivedAt.IsZero() || string(m.Key) != event.Source.DeviceID {
		return event, errors.New("invalid internal telemetry provenance or version")
	}
	return event, nil
}

// RunConsumer processes serially until cancellation or a transport/disposition
// failure. handler must be idempotent and honor context deadlines. Dependencies
// are caller-owned; this function never closes them or starts goroutines.
func RunConsumer(ctx context.Context, reader ConsumerReader, writer messageWriter, group string, policy ConsumerPolicy, logger *slog.Logger, handler func(context.Context, InternalEvent) error) error {
	if reader == nil || logger == nil || handler == nil || group == "" || policy.MaxAttempts < 1 || policy.Backoff <= 0 || policy.OperationTimeout <= 0 || (policy.Terminal != "stop" && policy.Terminal != "dead-letter") || (policy.Terminal == "dead-letter" && writer == nil) {
		return errors.New("invalid consumer configuration")
	}
	for {
		if err := ctx.Err(); err != nil {
			return err
		}
		m, err := reader.FetchMessage(ctx)
		if err != nil {
			return fmt.Errorf("fetch telemetry: %w", err)
		}
		if err := consumeRecord(ctx, reader, writer, group, policy, logger, handler, m); err != nil {
			return err
		}
	}
}

func consumeRecord(ctx context.Context, reader ConsumerReader, writer messageWriter, group string, policy ConsumerPolicy, logger *slog.Logger, handler func(context.Context, InternalEvent) error, m kafka.Message) error {
	event, decodeErr := decodeConsumerEvent(m)
	fields := []any{"consumer_group", group, "topic", m.Topic, "partition", m.Partition, "offset", m.Offset, "event_id", event.Source.EventID, "device_id", event.Source.DeviceID}
	var failure error
	attempts := 0
	for attempts < policy.MaxAttempts {
		if err := ctx.Err(); err != nil {
			return err
		}
		attempts++
		failure = decodeErr
		if failure == nil {
			attemptCtx, cancel := context.WithTimeout(ctx, policy.OperationTimeout)
			failure = handler(attemptCtx, event)
			if failure == nil {
				failure = attemptCtx.Err()
			}
			cancel()
		}
		if err := ctx.Err(); err != nil {
			return err
		}
		if failure == nil {
			break
		}
		logger.Warn("consumer_attempt_failed", append(fields, "attempt", attempts, "error", failure)...)
		if attempts < policy.MaxAttempts {
			timer := time.NewTimer(policy.Backoff)
			select {
			case <-ctx.Done():
				timer.Stop()
				return ctx.Err()
			case <-timer.C:
			}
		}
	}
	disposition := "processed"
	if failure != nil {
		if policy.Terminal == "stop" {
			return fmt.Errorf("consumer attempts exhausted: %w", failure)
		}
		value, err := json.Marshal(DeadLetter{"internal.dead-letter.v1", m.Topic, m.Partition, m.Offset, m.Key, m.Value, group, attempts, failure.Error(), time.Now().UTC()})
		if err != nil {
			return fmt.Errorf("encode dead letter: %w", err)
		}
		writeCtx, cancel := context.WithTimeout(ctx, policy.OperationTimeout)
		err = writer.WriteMessages(writeCtx, kafka.Message{Key: m.Key, Value: value})
		if err == nil {
			err = writeCtx.Err()
		}
		cancel()
		if err != nil {
			return fmt.Errorf("publish dead letter: %w", err)
		}
		disposition = "dead-lettered"
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	commitCtx, cancel := context.WithTimeout(ctx, policy.OperationTimeout)
	err := reader.CommitMessages(commitCtx, m)
	if err == nil {
		err = commitCtx.Err()
	}
	cancel()
	if err != nil {
		return fmt.Errorf("commit telemetry: %w", err)
	}
	logger.Info("consumer_disposition", append(fields, "attempts", attempts, "disposition", disposition)...)
	return nil
}
