package main

import (
	"flag"
	"fmt"
	"io"
	"strconv"

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
	flags.StringVar(&config.QuarantineDir, "quarantine-dir", config.QuarantineDir, "durable local quarantine directory (MACHINEPULSE_GATEWAY_QUARANTINE_DIR)")
	temperatureMin := flags.String("temperature-min", "", "optional inclusive temperature minimum in Celsius (MACHINEPULSE_GATEWAY_TEMPERATURE_MIN)")
	temperatureMax := flags.String("temperature-max", "", "optional inclusive temperature maximum in Celsius (MACHINEPULSE_GATEWAY_TEMPERATURE_MAX)")
	accelerationMax := flags.String("acceleration-max", "", "optional inclusive absolute acceleration maximum in m/s² (MACHINEPULSE_GATEWAY_ACCELERATION_MAX)")
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
		{"quarantine-dir", "MACHINEPULSE_GATEWAY_QUARANTINE_DIR"},
		{"temperature-min", "MACHINEPULSE_GATEWAY_TEMPERATURE_MIN"},
		{"temperature-max", "MACHINEPULSE_GATEWAY_TEMPERATURE_MAX"},
		{"acceleration-max", "MACHINEPULSE_GATEWAY_ACCELERATION_MAX"},
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
	for _, bound := range []struct {
		name, value string
		target      **float64
	}{
		{"temperature-min", *temperatureMin, &config.Validation.TemperatureMin},
		{"temperature-max", *temperatureMax, &config.Validation.TemperatureMax},
		{"acceleration-max", *accelerationMax, &config.Validation.AccelerationMax},
	} {
		if bound.value == "" {
			continue
		}
		value, err := strconv.ParseFloat(bound.value, 64)
		if err != nil {
			return config, fmt.Errorf("%s: must be a finite number", bound.name)
		}
		*bound.target = &value
	}
	if config.BrokerAddress == "" {
		return config, fmt.Errorf("MACHINEPULSE_MQTT_ADDRESS or --broker is required")
	}
	return config, config.Validate()
}
