//go:build integration

package gateway

import (
	"context"
	"encoding/json"
	"fmt"
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
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
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
}
