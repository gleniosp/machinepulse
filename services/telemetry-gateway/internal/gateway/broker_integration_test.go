//go:build integration

package gateway

import (
	"context"
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

	"github.com/eclipse/paho.golang/paho"
)

// Real Mosquitto proves protocol properties that handler fakes cannot: deferred
// PUBACK, receive-maximum backpressure, session resumption, and reconnects.
func TestBrokerSessionAndDeferredAcknowledgement(t *testing.T) {
	root, err := filepath.Abs("../../../..")
	if err != nil {
		t.Fatal(err)
	}
	project := fmt.Sprintf("machinepulse-gateway-test-%d", time.Now().UnixNano())
	// Docker may reassign a `:0` host binding on restart. Select a free port,
	// then give Compose a fixed binding for this isolated project's lifetime.
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	port := fmt.Sprint(listener.Addr().(*net.TCPAddr).Port)
	_ = listener.Close()
	compose := func(args ...string) string {
		t.Helper()
		ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
		defer cancel()
		base := []string{"compose", "--project-name", project, "--file", filepath.Join(root, "infra/docker/compose.yaml")}
		cmd := exec.CommandContext(ctx, "docker", append(base, args...)...)
		cmd.Env = append(os.Environ(), "MACHINEPULSE_MQTT_PORT="+port, "MACHINEPULSE_KAFKA_PORT=0")
		out, err := cmd.CombinedOutput()
		if err != nil {
			t.Fatalf("compose %v: %v\n%s", args, err, out)
		}
		return strings.TrimSpace(string(out))
	}
	t.Cleanup(func() { compose("down", "--volumes", "--remove-orphans") })
	compose("up", "--detach", "--wait", "--wait-timeout", "60", "mqtt")
	address := compose("port", "mqtt", "1883")
	payload, err := os.ReadFile(filepath.Join(root, "tools/simulator/tests/fixtures/telemetry.v1.json"))
	if err != nil {
		t.Fatal(err)
	}
	fixture := deliveryFor("", payload, time.Now())
	sourceJSON := string(payload)
	secondID := "650e8400-e29b-41d4-a716-446655440000"
	thirdID := "750e8400-e29b-41d4-a716-446655440000"
	config := DefaultConfig()
	config.BrokerAddress = address
	config.QuarantineDir = t.TempDir()
	config.ClientID = "gateway-integration"
	config.ReconnectCap = 200 * time.Millisecond
	var logs logBuffer
	t.Cleanup(func() {
		if t.Failed() {
			t.Log(logs.text())
		}
	})
	deliveries := make(chan Delivery, 10)
	start := func(durable bool, quarantine quarantineSink) func() {
		t.Helper()
		g, err := New(config, slog.New(slog.NewJSONHandler(&logs, nil)), func(_ context.Context, delivery Delivery) error {
			// Model a sink, without claiming these test acknowledgements persist data.
			deliveries <- delivery
			if !durable {
				return ErrNoDisposition
			}
			return nil
		})
		if err != nil {
			t.Fatal(err)
		}
		if quarantine != nil {
			g.quarantine = quarantine
		}
		ctx, cancel := context.WithCancel(context.Background())
		done := make(chan error, 1)
		go func() { done <- g.Run(ctx) }()
		return func() {
			cancel()
			select {
			case err := <-done:
				if err != nil {
					t.Error(err)
				}
			case <-time.After(5 * time.Second):
				t.Error("gateway did not stop")
			}
		}
	}
	receive := func() Delivery {
		t.Helper()
		select {
		case delivery := <-deliveries:
			return delivery
		case <-time.After(10 * time.Second):
			t.Fatalf("no delivery; logs:\n%s", logs.text())
			return Delivery{}
		}
	}
	stop := start(false, nil)
	t.Cleanup(func() { stop() })
	waitFor(t, func() bool { return strings.Contains(logs.text(), "mqtt_subscribed") }, "initial subscription")
	topic := "machinepulse/v1/telemetry/" + fixture.Source.DeviceID
	publish(t, address, topic, sourceJSON)
	first := receive()
	if string(first.Payload) != sourceJSON || first.Source.EventID == "" || first.Topic != topic {
		t.Fatalf("source changed: %+v", first)
	}
	publish(t, address, topic, strings.Replace(sourceJSON, fixture.Source.EventID, secondID, 1))
	select {
	case <-deliveries:
		t.Fatal("second delivery bypassed unacknowledged receive maximum")
	case <-time.After(200 * time.Millisecond):
	}
	stop()
	stop = start(true, nil)
	redelivered := receive()
	if string(redelivered.Payload) != string(first.Payload) || redelivered.Source != first.Source {
		t.Fatal("unacknowledged source not redelivered intact after restart")
	}
	if !redelivered.GatewayReceivedAt.After(first.GatewayReceivedAt) {
		t.Fatal("redelivery did not record a new separate receipt time")
	}
	second := receive()
	if second.Source.EventID == first.Source.EventID {
		t.Fatal("ack did not release next delivery")
	}
	waitFor(t, func() bool { return strings.Count(logs.text(), "telemetry_disposition_complete") >= 2 }, "sink success")
	// Allow Paho's periodic ack flush before shutting down the broker.
	time.Sleep(150 * time.Millisecond)
	compose("stop", "mqtt")
	waitFor(t, func() bool { return strings.Contains(logs.text(), "mqtt_connection_failed") }, "broker outage log")
	// Older supported Compose versions expose readiness waiting on up, not start.
	compose("up", "--detach", "--no-recreate", "--wait", "--wait-timeout", "60", "mqtt")
	waitFor(t, func() bool { return strings.Count(logs.text(), `"session_present":true`) >= 2 }, "session recovered after broker restart")
	if count := strings.Count(logs.text(), "mqtt_subscribed"); count != 1 {
		t.Fatalf("existing session was resubscribed: %d\n%s", count, logs.text())
	}
	publish(t, address, topic, strings.Replace(sourceJSON, fixture.Source.EventID, thirdID, 1))
	third := receive()
	if third.Source.EventID != thirdID {
		t.Fatalf("unexpected replay after durable ack: %s", third.Source.EventID)
	}
	// A real invalid delivery must reach disk and release the broker's receive
	// maximum before a subsequent valid delivery can reach the valid handler.
	publish(t, address, topic, "{")
	fourthID := "850e8400-e29b-41d4-a716-446655440000"
	publish(t, address, topic, strings.Replace(sourceJSON, fixture.Source.EventID, fourthID, 1))
	if fourth := receive(); fourth.Source.EventID != fourthID {
		t.Fatalf("invalid delivery blocked valid processing: %+v", fourth.Source)
	}
	records := readQuarantine(t, config.QuarantineDir)
	if len(records) != 1 || string(records[0].Payload) != "{" || records[0].Reason.Code != "invalid_json" {
		t.Fatalf("invalid delivery not durably recorded: %+v", records)
	}
	waitFor(t, func() bool { return strings.Count(logs.text(), "telemetry_disposition_complete") >= 5 }, "invalid disposition and next valid event")
	time.Sleep(150 * time.Millisecond)
	stop()
	stop = start(true, quarantineFunc(func(context.Context, Rejection) error { return errors.New("injected quarantine storage outage") }))
	invalidPayload := `{"event_id":17}`
	publish(t, address, topic, invalidPayload)
	fifthID := "950e8400-e29b-41d4-a716-446655440000"
	publish(t, address, topic, strings.Replace(sourceJSON, fixture.Source.EventID, fifthID, 1))
	waitFor(t, func() bool { return strings.Contains(logs.text(), "telemetry_quarantine_failed") }, "quarantine outage")
	select {
	case <-deliveries:
		t.Fatal("quarantine failure released next MQTT delivery")
	case <-time.After(200 * time.Millisecond):
	}
	stop()
	stop = start(true, nil)
	if fifth := receive(); fifth.Source.EventID != fifthID {
		t.Fatalf("recovered quarantine did not release next delivery: %+v", fifth.Source)
	}
	records = readQuarantine(t, config.QuarantineDir)
	if len(records) != 2 {
		t.Fatalf("expected two durable quarantine records after recovery, got %d", len(records))
	}
	found := false
	for _, record := range records {
		found = found || string(record.Payload) == invalidPayload
	}
	if !found {
		t.Fatal("failed quarantine payload was not redelivered intact")
	}
	t.Log("PASS: MQTT 5 QoS 1 subscription, source preservation, deferred PUBACK, backpressure, gateway/broker recovery, durable invalid disposition, quarantine failure redelivery and recovery")
}

func publish(t *testing.T, address, topic, payload string) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	conn, err := (&net.Dialer{}).DialContext(ctx, "tcp", address)
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()
	client := paho.NewClient(paho.ClientConfig{ClientID: "gateway-test-producer", Conn: conn})
	if _, err = client.Connect(ctx, &paho.Connect{ClientID: "gateway-test-producer", CleanStart: true, KeepAlive: 30}); err != nil {
		t.Fatal(err)
	}
	defer client.Disconnect(&paho.Disconnect{ReasonCode: 0})
	if _, err = client.Publish(ctx, &paho.Publish{Topic: topic, QoS: 1, Payload: []byte(payload)}); err != nil {
		t.Fatal(err)
	}
}
