package main

import (
	"errors"
	"flag"
	"io"
	"strings"
	"testing"
	"time"
)

func lookupMap(values map[string]string) func(string) (string, bool) {
	return func(key string) (string, bool) { value, ok := values[key]; return value, ok }
}

func TestConfigurationUsesDeploymentEnvironment(t *testing.T) {
	config, err := parseConfig(nil, lookupMap(map[string]string{
		"MACHINEPULSE_MQTT_ADDRESS":                "mqtt.staging.internal:21883",
		"MACHINEPULSE_MQTT_CLIENT_ID":              "staging-gateway-1",
		"MACHINEPULSE_MQTT_SESSION_EXPIRY_SECONDS": "3600",
		"MACHINEPULSE_MQTT_RECONNECT_CAP":          "30s",
		"MACHINEPULSE_MQTT_MAX_PACKET_BYTES":       "2097152",
		"MACHINEPULSE_GATEWAY_OPERATION_TIMEOUT":   "5s",
	}), io.Discard)
	if err != nil {
		t.Fatal(err)
	}
	if config.BrokerAddress != "mqtt.staging.internal:21883" || config.ClientID != "staging-gateway-1" ||
		config.SessionExpiry != 3600 || config.ReconnectCap != 30*time.Second ||
		config.MaximumPacketSize != 2097152 || config.OperationTimeout != 5*time.Second {
		t.Fatalf("environment not applied: %+v", config)
	}
}

func TestFlagsOverrideEnvironmentBeforeValidation(t *testing.T) {
	config, err := parseConfig([]string{"--broker", "[::1]:2883", "--session-expiry", "120"}, lookupMap(map[string]string{
		"MACHINEPULSE_MQTT_ADDRESS":                "invalid address",
		"MACHINEPULSE_MQTT_SESSION_EXPIRY_SECONDS": "invalid number",
	}), io.Discard)
	if err != nil {
		t.Fatal(err)
	}
	if config.BrokerAddress != "[::1]:2883" || config.SessionExpiry != 120 {
		t.Fatalf("flags not applied: %+v", config)
	}
}

func TestRequiredAddressHasNoImplicitLocalFallback(t *testing.T) {
	for _, values := range []map[string]string{nil, {"MACHINEPULSE_MQTT_ADDRESS": ""}} {
		_, err := parseConfig(nil, lookupMap(values), io.Discard)
		if err == nil || !strings.Contains(err.Error(), "MACHINEPULSE_MQTT_ADDRESS or --broker is required") {
			t.Fatalf("expected actionable required-address error, got %v", err)
		}
	}
}

func TestInvalidEnvironmentFailsAtStartup(t *testing.T) {
	for _, setting := range []struct{ key, value string }{
		{"MACHINEPULSE_MQTT_ADDRESS", "mqtt://localhost:1883"},
		{"MACHINEPULSE_MQTT_ADDRESS", "localhost:0"},
		{"MACHINEPULSE_MQTT_SESSION_EXPIRY_SECONDS", "many"},
		{"MACHINEPULSE_MQTT_SESSION_EXPIRY_SECONDS", "0"},
		{"MACHINEPULSE_MQTT_SESSION_EXPIRY_SECONDS", "4294967296"},
		{"MACHINEPULSE_MQTT_MAX_PACKET_BYTES", "-1"},
		{"MACHINEPULSE_MQTT_MAX_PACKET_BYTES", "4294967296"},
		{"MACHINEPULSE_MQTT_RECONNECT_CAP", "later"},
		{"MACHINEPULSE_GATEWAY_OPERATION_TIMEOUT", "0s"},
	} {
		t.Run(setting.key+"="+setting.value, func(t *testing.T) {
			values := map[string]string{"MACHINEPULSE_MQTT_ADDRESS": "mqtt:1883", setting.key: setting.value}
			if _, err := parseConfig(nil, lookupMap(values), io.Discard); err == nil {
				t.Fatal("invalid environment accepted")
			}
		})
	}
}

func TestHelpDoesNotRequireDeploymentConfiguration(t *testing.T) {
	_, err := parseConfig([]string{"--help"}, lookupMap(nil), io.Discard)
	if !errors.Is(err, flag.ErrHelp) {
		t.Fatalf("expected help, got %v", err)
	}
}
