//go:build integration

package gateway

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/segmentio/kafka-go"
)

func TestBrokerInternalTelemetry(t *testing.T) {
	root, err := filepath.Abs("../../../..")
	if err != nil {
		t.Fatal(err)
	}
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	port := fmt.Sprint(listener.Addr().(*net.TCPAddr).Port)
	listener.Close()
	project := fmt.Sprintf("machinepulse-stream-test-%d", time.Now().UnixNano())
	compose := func(args ...string) string {
		t.Helper()
		ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
		defer cancel()
		base := []string{"compose", "--project-name", project, "--file", filepath.Join(root, "infra/docker/compose.yaml")}
		cmd := exec.CommandContext(ctx, "docker", append(base, args...)...)
		cmd.Env = append(os.Environ(), "MACHINEPULSE_KAFKA_PORT="+port, "MACHINEPULSE_MQTT_PORT=0")
		out, err := cmd.CombinedOutput()
		if err != nil {
			t.Fatalf("compose %v: %v\n%s", args, err, out)
		}
		return strings.TrimSpace(string(out))
	}
	t.Cleanup(func() { compose("down", "--volumes", "--remove-orphans") })
	compose("up", "--detach", "--wait", "--wait-timeout", "90", "kafka")
	compose("exec", "-T", "kafka", "/opt/kafka/bin/kafka-topics.sh", "--bootstrap-server", "kafka:19092", "--create", "--topic", InternalTopic, "--partitions", "1", "--replication-factor", "1", "--config", "retention.ms=604800000", "--config", "cleanup.policy=delete")
	address := "127.0.0.1:" + port
	publisher := NewStreamPublisher(address, 10*time.Second)
	defer publisher.Close()
	payload, err := os.ReadFile(filepath.Join(root, "tools/simulator/tests/fixtures/telemetry.v1.json"))
	if err != nil {
		t.Fatal(err)
	}
	delivery := deliveryFor("", payload, time.Now())
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	if err := publisher.Publish(ctx, delivery); err != nil {
		t.Fatal(err)
	}
	reader := kafka.NewReader(kafka.ReaderConfig{Brokers: []string{address}, Topic: InternalTopic, Partition: 0, MaxBytes: 2 * 1024 * 1024})
	defer reader.Close()
	message, err := reader.ReadMessage(ctx)
	if err != nil {
		t.Fatal(err)
	}
	var event InternalEvent
	if err := json.Unmarshal(message.Value, &event); err != nil {
		t.Fatal(err)
	}
	if string(message.Key) != delivery.Source.DeviceID || event.Source != delivery.Source || event.SchemaVersion != InternalVersion {
		t.Fatal("stream consumer lost source provenance")
	}
	if !event.GatewayReceivedAt.Equal(delivery.GatewayReceivedAt) {
		t.Fatal("receipt time changed")
	}
	compose("exec", "-T", "kafka", "/opt/kafka/bin/kafka-topics.sh", "--bootstrap-server", "kafka:19092", "--create", "--topic", DeadLetterTopic, "--partitions", "1", "--replication-factor", "1")
	group := "consumer-disposition-test"
	consumer := NewConsumerReader(address, group)
	record, err := consumer.FetchMessage(ctx)
	if err != nil {
		t.Fatal(err)
	}
	deadWriter := NewDeadLetterWriter(address, 10*time.Second)
	defer deadWriter.Close()
	policy := ConsumerPolicy{MaxAttempts: 2, Backoff: time.Millisecond, OperationTimeout: 10 * time.Second, Terminal: "stop"}
	fail := func(context.Context, InternalEvent) error { return errors.New("injected sink failure") }
	if err := consumeRecord(ctx, consumer, deadWriter, group, policy, slog.Default(), fail, record); err == nil {
		t.Fatal("failure acknowledged")
	}
	if err := consumer.Close(); err != nil {
		t.Fatal(err)
	}
	consumer = NewConsumerReader(address, group)
	defer consumer.Close()
	repeated, err := consumer.FetchMessage(ctx)
	if err != nil {
		t.Fatal(err)
	}
	if repeated.Offset != record.Offset || string(repeated.Value) != string(record.Value) {
		t.Fatal("uncommitted record lost")
	}
	policy.Terminal = "dead-letter"
	if err := consumeRecord(ctx, consumer, deadWriter, group, policy, slog.Default(), fail, repeated); err != nil {
		t.Fatal(err)
	}
	deadReader := kafka.NewReader(kafka.ReaderConfig{Brokers: []string{address}, Topic: DeadLetterTopic, Partition: 0, MaxBytes: 4 * 1024 * 1024})
	defer deadReader.Close()
	deadMessage, err := deadReader.ReadMessage(ctx)
	if err != nil {
		t.Fatal(err)
	}
	var letter DeadLetter
	if err := json.Unmarshal(deadMessage.Value, &letter); err != nil {
		t.Fatal(err)
	}
	if string(letter.Value) != string(record.Value) || letter.Offset != record.Offset || letter.Reason != "injected sink failure" || letter.Attempts != 2 {
		t.Fatalf("dead letter lost failure/source: %+v", letter)
	}

}
