package gateway

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"log/slog"
	"os"
	"reflect"
	"testing"
	"time"

	"github.com/eclipse/paho.golang/paho"
	"github.com/segmentio/kafka-go"
)

type captureWriter struct {
	messages []kafka.Message
	err      error
}

func (w *captureWriter) WriteMessages(_ context.Context, messages ...kafka.Message) error {
	w.messages = append(w.messages, messages...)
	return w.err
}

func TestInternalEventFixture(t *testing.T) {
	fixture, err := os.ReadFile("testdata/internal.telemetry.v1.json")
	if err != nil {
		t.Fatal(err)
	}
	var expected InternalEvent
	if err := json.Unmarshal(fixture, &expected); err != nil {
		t.Fatal(err)
	}
	payload, err := os.ReadFile("../../../../tools/simulator/tests/fixtures/telemetry.v1.json")
	if err != nil {
		t.Fatal(err)
	}
	delivery := deliveryFor("machinepulse/v1/telemetry/"+expected.Source.DeviceID, payload, expected.GatewayReceivedAt)
	if reason := validateTelemetry(delivery, 1, false, ValidationPolicy{}); reason != nil {
		t.Fatal(reason)
	}
	writer := &captureWriter{}
	if err := publishEvent(context.Background(), writer, delivery); err != nil {
		t.Fatal(err)
	}
	if len(writer.messages) != 1 || string(writer.messages[0].Key) != expected.Source.DeviceID {
		t.Fatal("incorrect partition key")
	}
	var got, want any
	if err := json.Unmarshal(writer.messages[0].Value, &got); err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(fixture, &want); err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatal("producer differs from consumer fixture")
	}
	// Consumer decoding must retain all source fields and the full telemetry object.
	var event InternalEvent
	if err := json.Unmarshal(writer.messages[0].Value, &event); err != nil {
		t.Fatal(err)
	}
	decoded := deliveryFor("", event.Payload, time.Now())
	if event.SchemaVersion != InternalVersion || event.Source != decoded.Source || event.Source != delivery.Source {
		t.Fatal("source provenance changed")
	}
}

func TestStreamFailurePreventsMQTTAcknowledgement(t *testing.T) {
	payload, err := os.ReadFile("../../../../tools/simulator/tests/fixtures/telemetry.v1.json")
	if err != nil {
		t.Fatal(err)
	}
	delivery := deliveryFor("", payload, time.Now())
	failure := errors.New("stream unavailable")
	for _, result := range []error{failure, nil} {
		writer := &captureWriter{err: result}
		config := DefaultConfig()
		config.BrokerAddress = "localhost:1883"
		config.QuarantineDir = t.TempDir()
		g, err := New(config, slog.New(slog.NewTextHandler(io.Discard, nil)), func(ctx context.Context, d Delivery) error { return publishEvent(ctx, writer, d) })
		if err != nil {
			t.Fatal(err)
		}
		acknowledged := false
		err = g.receive(context.Background(), &paho.Publish{Topic: "machinepulse/v1/telemetry/" + delivery.Source.DeviceID, Payload: payload, QoS: 1}, func(*paho.Publish) error { acknowledged = true; return nil })
		if !errors.Is(err, result) || acknowledged != (result == nil) {
			t.Fatalf("err=%v acknowledged=%v", err, acknowledged)
		}
	}
}
