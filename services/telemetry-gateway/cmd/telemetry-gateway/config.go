package main

import (
	"flag"
	"fmt"
	"io"

	"github.com/gleniosp/machinepulse/services/telemetry-gateway/internal/gateway"
)

// parseConfig keeps environment lookup at the process boundary. The gateway
// library receives explicit configuration and never reads files or ambient env.
func parseConfig(args []string, lookup func(string) (string, bool), output io.Writer) (gateway.Config, error) {
	config := gateway.DefaultConfig()
	flags := flag.NewFlagSet("telemetry-gateway", flag.ContinueOnError)
	flags.SetOutput(output)
	flags.StringVar(&config.BrokerAddress, "broker", config.BrokerAddress, "MQTT host:port; required via flag or MACHINEPULSE_MQTT_ADDRESS")
	flags.StringVar(&config.ClientID, "client-id", config.ClientID, "stable deployment client ID (MACHINEPULSE_MQTT_CLIENT_ID)")
	expiry := flags.Uint64("session-expiry", uint64(config.SessionExpiry), "session expiry in seconds (MACHINEPULSE_MQTT_SESSION_EXPIRY_SECONDS)")
	limit := flags.Uint64("max-packet-bytes", uint64(config.MaximumPacketSize), "maximum inbound packet size (MACHINEPULSE_MQTT_MAX_PACKET_BYTES)")
	flags.DurationVar(&config.ReconnectCap, "reconnect-cap", config.ReconnectCap, "maximum reconnect delay (MACHINEPULSE_MQTT_RECONNECT_CAP)")
	flags.DurationVar(&config.OperationTimeout, "operation-timeout", config.OperationTimeout, "operation deadline (MACHINEPULSE_GATEWAY_OPERATION_TIMEOUT)")
	if err := flags.Parse(args); err != nil {
		return config, err
	}
	if flags.NArg() != 0 {
		return config, fmt.Errorf("positional arguments are unsupported")
	}
	explicit := make(map[string]bool)
	flags.Visit(func(f *flag.Flag) { explicit[f.Name] = true })
	for _, setting := range []struct{ flag, env string }{
		{"broker", "MACHINEPULSE_MQTT_ADDRESS"},
		{"client-id", "MACHINEPULSE_MQTT_CLIENT_ID"},
		{"session-expiry", "MACHINEPULSE_MQTT_SESSION_EXPIRY_SECONDS"},
		{"max-packet-bytes", "MACHINEPULSE_MQTT_MAX_PACKET_BYTES"},
		{"reconnect-cap", "MACHINEPULSE_MQTT_RECONNECT_CAP"},
		{"operation-timeout", "MACHINEPULSE_GATEWAY_OPERATION_TIMEOUT"},
	} {
		if explicit[setting.flag] {
			continue
		}
		if value, ok := lookup(setting.env); ok && value != "" {
			if err := flags.Set(setting.flag, value); err != nil {
				return config, fmt.Errorf("%s: %w", setting.env, err)
			}
		}
	}
	if *expiry > uint64(^uint32(0)) || *limit > uint64(^uint32(0)) {
		return config, fmt.Errorf("session expiry and packet limit must fit uint32")
	}
	config.SessionExpiry, config.MaximumPacketSize = uint32(*expiry), uint32(*limit)
	if config.BrokerAddress == "" {
		return config, fmt.Errorf("MACHINEPULSE_MQTT_ADDRESS or --broker is required")
	}
	return config, config.Validate()
}
