package gateway

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/eclipse/paho.golang/paho"
)

func validatePayload(payload string, policy ValidationPolicy) *ValidationError {
	return validateTelemetry(deliveryFor(sourceTopic, []byte(payload), time.Now()), 1, false, policy)
}

func TestSharedProducerContractFixtures(t *testing.T) {
	directory := "../../../../tools/simulator/tests/fixtures"
	paths, err := filepath.Glob(filepath.Join(directory, "telemetry-invalid/*.json"))
	if err != nil || len(paths) == 0 {
		t.Fatalf("contract fixture corpus: %v, %v", paths, err)
	}
	paths = append(paths, filepath.Join(directory, "telemetry.v1.json"))
	for _, path := range paths {
		t.Run(filepath.Base(path), func(t *testing.T) {
			payload, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			d := deliveryFor("machinepulse/v1/telemetry/01M000000028T5CY4GNF6YY4HM", payload, time.Now())
			reason := validateTelemetry(d, 1, false, ValidationPolicy{})
			valid := filepath.Base(path) == "telemetry.v1.json"
			if (reason == nil) != valid {
				t.Fatalf("unexpected result: %v", reason)
			}
			if reason != nil && (reason.Path == "" || reason.Code == "" || reason.Message == "") {
				t.Fatalf("unactionable error: %+v", reason)
			}
		})
	}
}

func TestIngressRejectsAmbiguousAndInvalidWireValues(t *testing.T) {
	for _, tc := range []struct{ name, payload, code string }{
		{"null", "null", "type"},
		{"array", "[]", "type"},
		{"malformed", "{", "invalid_json"},
		{"trailing", sourceJSON + " {}", "invalid_json"},
		{"utf8", "{\"bad\":\"" + string([]byte{255}) + "\"}", "invalid_json"},
		{"duplicate", strings.Replace(sourceJSON, `"sequence":9007199254740993`, `"sequence":0,"sequence":1`, 1), "duplicate_key"},
		{"nested duplicate", strings.Replace(sourceJSON, `"x":[0.1]`, `"x":[0.1],"x":[1]`, 1), "duplicate_key"},
		{"unknown", strings.Replace(sourceJSON, `"temperature_c":40`, `"temperatur_c":40,"temperature_c":40`, 1), "unknown_field"},
		{"unknown root", strings.Replace(sourceJSON, `"sequence":9007199254740993`, `"label":"normal","sequence":0`, 1), "unknown_field"},
		{"null sampling", strings.Replace(sourceJSON, `{"rate_hz":1,"sample_count":1,"window_duration_ms":1000}`, "null", 1), "type"},
		{"null axis", strings.Replace(sourceJSON, `"x":[0.1]`, `"x":null`, 1), "type"},
		{"axis count", strings.Replace(sourceJSON, `"x":[0.1]`, `"x":[]`, 1), "sample_count"},
		{"boolean measurement", strings.Replace(sourceJSON, `"temperature_c":40`, `"temperature_c":true`, 1), "finite_number"},
		{"null measurement", strings.Replace(sourceJSON, `"temperature_c":40`, `"temperature_c":null`, 1), "finite_number"},
		{"string sample", strings.Replace(sourceJSON, `"x":[0.1]`, `"x":["0.1"]`, 1), "finite_number"},
		{"overflow number", strings.Replace(sourceJSON, `"x":[0.1]`, `"x":[1e400]`, 1), "finite_number"},
		{"boolean sequence", strings.Replace(sourceJSON, `9007199254740993`, `true`, 1), "integer"},
		{"negative sequence", strings.Replace(sourceJSON, `9007199254740993`, `-1`, 1), "integer"},
		{"decimal sequence", strings.Replace(sourceJSON, `9007199254740993`, `1.0`, 1), "integer"},
		{"zero rate", strings.Replace(sourceJSON, `"rate_hz":1`, `"rate_hz":0`, 1), "integer"},
		{"sampling overflow", strings.Replace(sourceJSON, `"window_duration_ms":1000`, `"window_duration_ms":18446744073709552616`, 1), "duration_mismatch"},
		{"one interval", strings.Replace(sourceJSON, `"window_duration_ms":1000`, `"window_duration_ms":2000`, 1), "duration_mismatch"},
		{"noncanonical uuid", strings.Replace(sourceJSON, "09f5ca55", "09F5CA55", 1), "identifier"},
		{"overflow ulid", strings.Replace(sourceJSON, "01ARZ3NDEKTSV4RRFFQ69G5FAV", "81ARZ3NDEKTSV4RRFFQ69G5FAV", 1), "identifier"},
		{"lowercase ulid", strings.Replace(sourceJSON, "01ARZ3NDEKTSV4RRFFQ69G5FAW", "01arz3ndektsv4rrffq69g5faw", 1), "identifier"},
		{"nonUTC", strings.Replace(sourceJSON, "00:00:00.000000Z", "00:00:00+01:00", 1), "utc_timestamp"},
		{"naive", strings.Replace(sourceJSON, "00:00:00.000000Z", "00:00:00", 1), "utc_timestamp"},
		{"depth", strings.Repeat("[", 65) + strings.Repeat("]", 65), "nesting_limit"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			reason := validatePayload(tc.payload, ValidationPolicy{})
			if reason == nil || reason.Code != tc.code {
				t.Fatalf("expected %s, got %+v", tc.code, reason)
			}
		})
	}
}

func TestValidPayloadAndInclusiveConfiguredBounds(t *testing.T) {
	minimum, maximum, acceleration := 40.0, 40.0, 0.1
	policy := ValidationPolicy{&minimum, &maximum, &acceleration}
	for _, payload := range []string{
		sourceJSON,
		strings.Replace(sourceJSON, "00:00:00.000000Z", "00:00:00+00:00", 1),
		strings.Replace(sourceJSON, "T00:00:00.000000Z", " 00:00:00.000000Z", 1),
		strings.Replace(sourceJSON, `"window_duration_ms":1000`, `"window_duration_ms":1999`, 1),
	} {
		if reason := validatePayload(payload, policy); reason != nil {
			t.Fatal(reason)
		}
	}
	for _, replacement := range []struct{ before, after, path string }{
		{`"temperature_c":40`, `"temperature_c":39.9`, "measurements.temperature_c"},
		{`"temperature_c":40`, `"temperature_c":40.1`, "measurements.temperature_c"},
		{`"x":[0.1]`, `"x":[-0.1001]`, "measurements.vibration_m_s2.x[0]"},
	} {
		payload := strings.Replace(sourceJSON, replacement.before, replacement.after, 1)
		reason := validatePayload(payload, policy)
		if reason == nil || reason.Code != "configured_bound" || reason.Path != replacement.path {
			t.Fatalf("unexpected bound result: %+v", reason)
		}
		if reason := validatePayload(payload, ValidationPolicy{}); reason != nil {
			t.Fatalf("unset policy rejected finite value: %v", reason)
		}
	}
}

func TestTopicIdentityAndDeliveryPolicy(t *testing.T) {
	for _, tc := range []struct {
		topic    string
		qos      byte
		retained bool
	}{
		{"other/topic", 1, false}, {sourceTopic + "/extra", 1, false}, {sourceTopic, 0, false}, {sourceTopic, 1, true},
	} {
		d := deliveryFor(tc.topic, []byte(sourceJSON), time.Now())
		if validateTelemetry(d, tc.qos, tc.retained, ValidationPolicy{}) == nil {
			t.Fatalf("accepted invalid route/delivery: %+v", tc)
		}
	}
}

func TestValidationDoesNotModifySourceOrDeduplicate(t *testing.T) {
	calls := 0
	g := testGateway(t, func(_ context.Context, d Delivery) error {
		calls++
		if string(d.Payload) != sourceJSON || d.Source.OccurredAt != "2026-10-01T00:00:00.000000Z" {
			t.Fatal("source changed")
		}
		return nil
	}, &logBuffer{})
	for range 2 {
		if err := g.receive(context.Background(), sourcePacket(), func(*paho.Publish) error { return nil }); err != nil {
			t.Fatal(err)
		}
	}
	if calls != 2 || g.Counters().Valid != 2 {
		t.Fatalf("duplicate was suppressed: %d %+v", calls, g.Counters())
	}
}
