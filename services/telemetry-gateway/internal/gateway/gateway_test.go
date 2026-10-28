package gateway

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/eclipse/paho.golang/packets"
	"github.com/eclipse/paho.golang/paho"
)

const sourceJSON = `{"event_id":"09f5ca55-ec6a-50cb-9dc0-caa53d0d4171","device_id":"01ARZ3NDEKTSV4RRFFQ69G5FAV","asset_id":"01ARZ3NDEKTSV4RRFFQ69G5FAW","occurred_at":"2026-10-01T00:00:00.000000Z","schema_version":"telemetry.v1","sequence":9007199254740993,"sampling":{"rate_hz":1,"sample_count":1,"window_duration_ms":1000},"measurements":{"temperature_c":40,"rpm":1800,"vibration_m_s2":{"x":[0.1],"y":[0],"z":[-0.1]}}}`

const sourceTopic = "machinepulse/v1/telemetry/01ARZ3NDEKTSV4RRFFQ69G5FAV"

func testGateway(t *testing.T, handler Handler, output io.Writer) *Gateway {
	t.Helper()
	config := DefaultConfig()
	config.BrokerAddress = "127.0.0.1:1883"
	config.QuarantineDir = t.TempDir()
	g, err := New(config, slog.New(slog.NewJSONHandler(output, nil)), handler)
	if err != nil {
		t.Fatal(err)
	}
	return g
}

func TestDecodePreservesProducerBytesAndSeparateReceipt(t *testing.T) {
	payload := []byte(sourceJSON)
	receipt := time.Date(2026, 10, 16, 12, 0, 0, 123, time.FixedZone("local", 7200))
	d := deliveryFor(sourceTopic, payload, receipt)
	payload[0] = ' '
	if string(d.Payload) != sourceJSON || d.Source.OccurredAt != "2026-10-01T00:00:00.000000Z" {
		t.Fatalf("producer data changed: %+v", d)
	}
	if d.GatewayReceivedAt.Location() != time.UTC || !d.GatewayReceivedAt.Equal(receipt) {
		t.Fatalf("receipt must be separate UTC time: %v", d.GatewayReceivedAt)
	}
}

func TestReceiveAcknowledgesOnlyDurableSuccess(t *testing.T) {
	for _, result := range []error{nil, ErrNoDisposition, errors.New("sink unavailable")} {
		t.Run(fmtError(result), func(t *testing.T) {
			processed, acknowledged := false, false
			g := testGateway(t, func(_ context.Context, d Delivery) error {
				if d.Source.DeviceID == "" || string(d.Payload) != sourceJSON {
					t.Fatal("producer data missing")
				}
				processed = true
				return result
			}, io.Discard)
			err := g.receive(context.Background(), &paho.Publish{QoS: 1, Topic: sourceTopic, Payload: []byte(sourceJSON)}, func(*paho.Publish) error {
				if !processed || result != nil {
					t.Fatal("ack before durable success")
				}
				acknowledged = true
				return nil
			})
			if !errors.Is(err, result) || acknowledged != (result == nil) {
				t.Fatalf("result %v, ack %v", err, acknowledged)
			}
		})
	}
}

func fmtError(err error) string {
	if err == nil {
		return "durable success"
	}
	return err.Error()
}

func TestMalformedOrUnsupportedDeliveryIsQuarantinedBeforeAcknowledgement(t *testing.T) {
	cases := []paho.Publish{
		{QoS: 1, Payload: []byte(`{`)},
		{QoS: 1, Payload: []byte(`null`)},
		{QoS: 1, Payload: []byte(`[]`)},
		{QoS: 1, Payload: []byte(`{} {}`)},
		{QoS: 1, Payload: []byte(`{"event_id":123}`)},
		{QoS: 0, Payload: []byte(sourceJSON)},
		{QoS: 1, Retain: true, Payload: []byte(sourceJSON)},
	}
	g := testGateway(t, func(context.Context, Delivery) error { t.Fatal("handler called"); return nil }, io.Discard)
	for _, packet := range cases {
		acknowledged := false
		before := g.Counters().Quarantined
		if err := g.receive(context.Background(), &packet, func(*paho.Publish) error {
			if g.Counters().Quarantined != before+1 {
				t.Fatal("ack before quarantine")
			}
			acknowledged = true
			return nil
		}); err != nil {
			t.Fatal(err)
		}
		if acknowledged != (packet.QoS == 1) {
			t.Fatalf("unexpected ack for QoS %d", packet.QoS)
		}
	}
}

func TestCancellationDuringDispositionDoesNotAcknowledge(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	g := testGateway(t, func(context.Context, Delivery) error { cancel(); return nil }, io.Discard)
	err := g.receive(ctx, &paho.Publish{QoS: 1, Topic: sourceTopic, Payload: []byte(sourceJSON)}, func(*paho.Publish) error { t.Fatal("ack called"); return nil })
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("expected cancellation, got %v", err)
	}
}

type logBuffer struct {
	mu sync.Mutex
	bytes.Buffer
}

func (b *logBuffer) Write(p []byte) (int, error) {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.Buffer.Write(p)
}

func (b *logBuffer) text() string {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.Buffer.String()
}

func waitFor(t *testing.T, predicate func() bool, detail string) {
	t.Helper()
	deadline := time.Now().Add(15 * time.Second)
	for time.Now().Before(deadline) {
		if predicate() {
			return
		}
		time.Sleep(10 * time.Millisecond)
	}
	t.Fatalf("timed out: %s", detail)
}

func TestConnectionFailureIsLoggedAndBackoffCanBeCancelled(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	address := listener.Addr().String()
	_ = listener.Close()
	var logs logBuffer
	g := testGateway(t, func(context.Context, Delivery) error { return ErrNoDisposition }, &logs)
	g.config.BrokerAddress = address
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	done := make(chan error, 1)
	go func() { done <- g.Run(ctx) }()
	waitFor(t, func() bool { return strings.Contains(logs.text(), "mqtt_connection_failed") }, "connection failure log")
	cancel()
	select {
	case err := <-done:
		if err != nil {
			t.Fatal(err)
		}
	case <-time.After(time.Second):
		t.Fatal("cancellation did not interrupt reconnect backoff")
	}
}

func TestConfigurationRejectsEphemeralSessionsAndInvalidLimits(t *testing.T) {
	for _, change := range []func(*Config){
		func(c *Config) { c.ClientID = " " },
		func(c *Config) { c.SessionExpiry = 0 },
		func(c *Config) { c.ReconnectCap = 0 },
		func(c *Config) { c.OperationTimeout = 0 },
		func(c *Config) { c.MaximumPacketSize = 0 },
		func(c *Config) { c.QuarantineDir = " " },
		func(c *Config) { c.BrokerAddress = "mqtt://localhost" },
		func(c *Config) { c.BrokerAddress = "" },
		func(c *Config) { c.BrokerAddress = "host name:1883" },
	} {
		config := DefaultConfig()
		config.BrokerAddress = "127.0.0.1:1883"
		change(&config)
		if config.Validate() == nil {
			t.Errorf("invalid config accepted: %+v", config)
		}
	}
}

func TestRejectedSubscriptionIsRetriedInExistingSession(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	serverDone := make(chan error, 1)
	t.Cleanup(func() {
		if t.Failed() {
			select {
			case err := <-serverDone:
				t.Logf("protocol server: %v", err)
			default:
			}
		}
	})
	go func() {
		for attempt := 0; attempt < 2; attempt++ {
			conn, err := listener.Accept()
			if err != nil {
				serverDone <- err
				return
			}
			err = func() error {
				defer conn.Close()
				_ = conn.SetDeadline(time.Now().Add(5 * time.Second))
				readControl := func() (*packets.ControlPacket, error) {
					for {
						packet, err := packets.ReadPacket(conn)
						if err != nil || packet.Type != packets.PINGREQ {
							return packet, err
						}
						if _, err := packets.NewControlPacket(packets.PINGRESP).WriteTo(conn); err != nil {
							return nil, err
						}
					}
				}
				if _, err := readControl(); err != nil {
					return err
				}
				if _, err := (&packets.Connack{SessionPresent: attempt == 1, Properties: &packets.Properties{}}).WriteTo(conn); err != nil {
					return err
				}
				packet, err := readControl()
				if err != nil {
					return err
				}
				sub, ok := packet.Content.(*packets.Subscribe)
				if !ok {
					return fmt.Errorf("expected SUBSCRIBE on attempt %d, got %T", attempt, packet.Content)
				}
				reason := byte(0x87) // Reject initial subscription; preserve the broker session.
				if attempt == 1 {
					reason = 1
				}
				if _, err := (&packets.Suback{PacketID: sub.PacketID, Reasons: []byte{reason}, Properties: &packets.Properties{}}).WriteTo(conn); err != nil {
					return err
				}
				_, err = readControl() // Read the gateway's DISCONNECT.
				return err
			}()
			if err != nil {
				serverDone <- err
				return
			}
		}
		serverDone <- nil
	}()
	var logs logBuffer
	g := testGateway(t, func(context.Context, Delivery) error { return ErrNoDisposition }, &logs)
	g.config.BrokerAddress = listener.Addr().String()
	t.Cleanup(func() {
		if t.Failed() {
			t.Log(logs.text())
		}
	})
	g.config.ReconnectCap = time.Millisecond
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	done := make(chan error, 1)
	go func() { done <- g.Run(ctx) }()
	waitFor(t, func() bool { return strings.Contains(logs.text(), `"msg":"mqtt_connected","session_present":true`) }, "subscription recovery in an existing session")
	cancel()
	select {
	case <-done:
	case <-time.After(time.Second):
		t.Fatal("gateway did not stop")
	}
	select {
	case err := <-serverDone:
		if err != nil {
			t.Fatal(err)
		}
	case <-time.After(6 * time.Second):
		t.Fatal("protocol server did not finish")
	}
}
