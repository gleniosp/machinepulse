package gateway

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"math/rand/v2"
	"net"
	"strconv"
	"strings"
	"sync/atomic"
	"time"

	"github.com/eclipse/paho.golang/paho"
)

const TopicFilter = "machinepulse/v1/telemetry/+"

var ErrNoDisposition = errors.New("durable disposition is not configured")

// Handler must return nil only after a durable terminal disposition. It must
// honor ctx and must not retain references to a client or acknowledge MQTT itself.
// P02-005 supplies the command's durable valid-event sink.
type Handler func(context.Context, Delivery) error

type Config struct {
	BrokerAddress     string
	ClientID          string
	SessionExpiry     uint32
	ReconnectCap      time.Duration
	OperationTimeout  time.Duration
	MaximumPacketSize uint32
	QuarantineDir     string
	Validation        ValidationPolicy
}

// DefaultConfig supplies tuning defaults. Callers must provide BrokerAddress.
func DefaultConfig() Config {
	return Config{
		ClientID:      "machinepulse-gateway-local",
		SessionExpiry: 86400, ReconnectCap: time.Minute,
		OperationTimeout: 10 * time.Second, MaximumPacketSize: 1024 * 1024,
		QuarantineDir: "gateway-quarantine",
	}
}

func (c Config) Validate() error {
	if strings.TrimSpace(c.BrokerAddress) == "" {
		return errors.New("broker address is required")
	}
	host, port, err := net.SplitHostPort(c.BrokerAddress)
	if err != nil {
		return fmt.Errorf("broker must be host:port: %w", err)
	}
	portNumber, err := strconv.ParseUint(port, 10, 16)
	if err != nil || portNumber == 0 || strings.TrimSpace(host) == "" || strings.ContainsAny(host, "/ \t\r\n") {
		return errors.New("broker must have a host and numeric port between 1 and 65535")
	}
	if strings.TrimSpace(c.ClientID) == "" || c.SessionExpiry == 0 || c.ReconnectCap <= 0 || c.OperationTimeout <= 0 || c.MaximumPacketSize == 0 {
		return errors.New("client ID, session expiry, reconnect cap, operation timeout, and packet limit must be nonzero")
	}
	if strings.TrimSpace(c.QuarantineDir) == "" {
		return errors.New("quarantine directory is required")
	}
	return c.Validation.Validate()
}

// ValidationCounters count attempts for this process, including redeliveries.
// Valid means stateless validation passed, not durable downstream acceptance.
type ValidationCounters struct {
	Received, Valid, Invalid, Quarantined, QuarantineFailed uint64
}

type validationMetrics struct {
	received, valid, invalid, quarantined, quarantineFailed atomic.Uint64
}

type Gateway struct {
	config     Config
	logger     *slog.Logger
	handle     Handler
	quarantine quarantineSink
	metrics    validationMetrics
	// Only the connection loop accesses this flag. A session may exist even
	// when the previous SUBSCRIBE was rejected or its acknowledgement was lost.
	subscriptionPending bool
}

func New(config Config, logger *slog.Logger, handle Handler) (*Gateway, error) {
	if err := config.Validate(); err != nil {
		return nil, err
	}
	if logger == nil || handle == nil {
		return nil, errors.New("logger and durable-disposition handler are required")
	}
	quarantine, err := newFileQuarantine(config.QuarantineDir)
	if err != nil {
		return nil, err
	}
	return &Gateway{config: config, logger: logger, handle: handle, quarantine: quarantine}, nil
}

func (g *Gateway) Counters() ValidationCounters {
	return ValidationCounters{
		Received: g.metrics.received.Load(), Valid: g.metrics.valid.Load(), Invalid: g.metrics.invalid.Load(),
		Quarantined: g.metrics.quarantined.Load(), QuarantineFailed: g.metrics.quarantineFailed.Load(),
	}
}

func (g *Gateway) logCounters() {
	c := g.Counters()
	g.logger.Info("telemetry_validation_counters", "received_total", c.Received, "valid_total", c.Valid,
		"invalid_total", c.Invalid, "quarantined_total", c.Quarantined, "quarantine_failed_total", c.QuarantineFailed)
}

// Run reconnects until cancellation. Each connection owns a separate Paho
// client/session; no acknowledgement can cross into a replacement connection.
func (g *Gateway) Run(ctx context.Context) error {
	delay := min(time.Second, g.config.ReconnectCap)
	for ctx.Err() == nil {
		connected, err := g.connect(ctx)
		if ctx.Err() != nil {
			break
		}
		if connected {
			delay = min(time.Second, g.config.ReconnectCap)
		}
		// Equal jitter: wait between half the current delay and the full delay.
		wait := delay/2 + time.Duration(rand.Int64N(max(int64(delay-delay/2), 1)))
		g.logger.Error("mqtt_connection_failed", "error", err, "retry_in", wait.String())
		timer := time.NewTimer(wait)
		select {
		case <-ctx.Done():
			timer.Stop()
		case <-timer.C:
		}
		if delay < g.config.ReconnectCap/2 {
			delay *= 2
		} else {
			delay = g.config.ReconnectCap
		}
	}
	g.logger.Info("gateway_stopped")
	return nil
}

func (g *Gateway) connect(ctx context.Context) (bool, error) {
	g.logger.Info("mqtt_connecting", "broker", g.config.BrokerAddress, "client_id", g.config.ClientID)
	conn, err := (&net.Dialer{Timeout: g.config.OperationTimeout}).DialContext(ctx, "tcp", g.config.BrokerAddress)
	if err != nil {
		return false, err
	}
	defer conn.Close()
	client := paho.NewClient(paho.ClientConfig{
		ClientID: g.config.ClientID, Conn: conn, PacketTimeout: g.config.OperationTimeout,
		EnableManualAcknowledgment: true,
		OnClientError: func(err error) {
			if ctx.Err() == nil {
				g.logger.Error("mqtt_connection_lost", "error", err)
			}
		},
		OnServerDisconnect: func(d *paho.Disconnect) { g.logger.Error("mqtt_server_disconnect", "reason_code", d.ReasonCode) },
		OnPublishReceived: []func(paho.PublishReceived) (bool, error){func(received paho.PublishReceived) (bool, error) {
			return true, g.receive(ctx, received.Packet, received.Client.Ack)
		}},
	})
	// One unacknowledged QoS 1 delivery bounds in-flight application work. A
	// failed/missing durable sink applies broker backpressure instead of loss.
	receiveMaximum := uint16(1)
	connectCtx, cancel := context.WithTimeout(ctx, g.config.OperationTimeout)
	ack, err := client.Connect(connectCtx, &paho.Connect{
		ClientID: g.config.ClientID, CleanStart: false, KeepAlive: 30,
		Properties: &paho.ConnectProperties{
			SessionExpiryInterval: &g.config.SessionExpiry, ReceiveMaximum: &receiveMaximum,
			MaximumPacketSize: &g.config.MaximumPacketSize,
		},
	})
	cancel()
	if err != nil {
		return false, fmt.Errorf("MQTT 5 connect: %w", err)
	}
	defer func() {
		// Bound shutdown writes even when a peer has stopped reading.
		_ = conn.SetWriteDeadline(time.Now().Add(g.config.OperationTimeout))
		_ = client.Disconnect(&paho.Disconnect{ReasonCode: 0})
	}()
	if !ack.SessionPresent {
		g.subscriptionPending = true
	}
	if g.subscriptionPending {
		subscribeCtx, cancel := context.WithTimeout(ctx, g.config.OperationTimeout)
		result, err := client.Subscribe(subscribeCtx, &paho.Subscribe{Subscriptions: []paho.SubscribeOptions{{
			Topic: TopicFilter, QoS: 1, RetainHandling: 2, RetainAsPublished: true,
		}}})
		cancel()
		if err != nil {
			return false, fmt.Errorf("subscribe: %w", err)
		}
		if len(result.Reasons) != 1 || result.Reasons[0] != 1 {
			return false, fmt.Errorf("subscription did not grant QoS 1: %v", result.Reasons)
		}
		g.subscriptionPending = false
		g.logger.Info("mqtt_subscribed", "topic", TopicFilter, "qos", 1)
	}
	g.logger.Info("mqtt_connected", "session_present", ack.SessionPresent)
	select {
	case <-ctx.Done():
		return true, ctx.Err()
	case <-client.Done():
		return true, errors.New("MQTT connection ended")
	}
}

func (g *Gateway) receive(ctx context.Context, packet *paho.Publish, ack func(*paho.Publish) error) error {
	if ctx.Err() != nil {
		return ctx.Err()
	}
	g.metrics.received.Add(1)
	defer g.logCounters()
	delivery := deliveryFor(packet.Topic, packet.Payload, time.Now())
	fields := []any{"event_id", delivery.Source.EventID, "device_id", delivery.Source.DeviceID,
		"asset_id", delivery.Source.AssetID, "occurred_at", delivery.Source.OccurredAt,
		"gateway_received_at", delivery.GatewayReceivedAt.Format(time.RFC3339Nano), "topic", packet.Topic}
	g.logger.Info("telemetry_received", fields...)
	handlerCtx, cancel := context.WithTimeout(ctx, g.config.OperationTimeout)
	defer cancel()
	var err error
	if reason := validateTelemetry(delivery, packet.QoS, packet.Retain, g.config.Validation); reason != nil {
		g.metrics.invalid.Add(1)
		g.logger.Warn("telemetry_rejected", append(fields, "reason_code", reason.Code, "path", reason.Path, "error", reason.Message)...)
		err = g.quarantine.Store(handlerCtx, rejection(delivery, packet.QoS, packet.Retain, reason))
		if err == nil {
			err = handlerCtx.Err()
		}
		if err != nil {
			g.metrics.quarantineFailed.Add(1)
			g.logger.Error("telemetry_quarantine_failed", append(fields, "error", err)...)
		} else {
			g.metrics.quarantined.Add(1)
			g.logger.Info("telemetry_quarantined", fields...)
		}
	} else {
		g.metrics.valid.Add(1)
		err = g.handle(handlerCtx, delivery)
	}
	if err == nil {
		err = handlerCtx.Err()
	}
	if err == nil && packet.QoS == 1 {
		err = ack(packet)
	}
	if err != nil {
		g.logger.Warn("telemetry_unacknowledged", append(fields, "error", err)...)
		return err
	}
	g.logger.Info("telemetry_disposition_complete", fields...)
	return nil
}
