package gateway

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"math/big"
	"regexp"
	"slices"
	"strings"
	"time"
	"unicode/utf8"
)

// ValidationPolicy contains inclusive deployment bounds, not physical truths.
// Nil disables a bound. Stateless telemetry.v1 checks always apply.
type ValidationPolicy struct {
	TemperatureMin  *float64
	TemperatureMax  *float64
	AccelerationMax *float64
}

func (p ValidationPolicy) Validate() error {
	for _, bound := range []*float64{p.TemperatureMin, p.TemperatureMax, p.AccelerationMax} {
		if bound != nil && (math.IsNaN(*bound) || math.IsInf(*bound, 0)) {
			return errors.New("measurement bounds must be finite")
		}
	}
	if p.TemperatureMin != nil && p.TemperatureMax != nil && *p.TemperatureMin > *p.TemperatureMax {
		return errors.New("temperature minimum must not exceed maximum")
	}
	if p.AccelerationMax != nil && *p.AccelerationMax < 0 {
		return errors.New("maximum absolute acceleration must be non-negative")
	}
	return nil
}

// ValidationError identifies the first failure without including payload values.
type ValidationError struct {
	Path    string `json:"path"`
	Code    string `json:"code"`
	Message string `json:"message"`
}

func (e *ValidationError) Error() string { return e.Path + ": " + e.Message }

func invalid(path, code, message string) *ValidationError {
	return &ValidationError{Path: path, Code: code, Message: message}
}

var (
	uuidPattern = regexp.MustCompile(`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`)
	ulidPattern = regexp.MustCompile(`^[0-7][0-9A-HJKMNP-TV-Z]{25}$`)
)

// validateTelemetry never rewrites the payload. It uses exact integers for
// sampling arithmetic, so overflow cannot turn an invalid duration into a pass.
func validateTelemetry(d Delivery, qos byte, retained bool, policy ValidationPolicy) *ValidationError {
	if qos != 1 || retained {
		return invalid("mqtt", "delivery_policy", "expected non-retained QoS 1 telemetry")
	}
	if !utf8.Valid(d.Payload) {
		return invalid("payload", "invalid_json", "must contain valid UTF-8 JSON")
	}
	decoder := json.NewDecoder(bytes.NewReader(d.Payload))
	decoder.UseNumber()
	value, err := readJSON(decoder, "payload", 0)
	if err != nil {
		return err
	}
	if _, err := decoder.Token(); err != io.EOF {
		return invalid("payload", "invalid_json", "must contain exactly one JSON object")
	}
	root, err := object(value, "payload", "schema_version", "event_id", "device_id", "asset_id", "occurred_at", "sequence", "sampling", "measurements")
	if err != nil {
		return err
	}
	if root["schema_version"] != "telemetry.v1" {
		return invalid("schema_version", "unsupported_version", "must be telemetry.v1")
	}
	for _, field := range []string{"event_id", "device_id", "asset_id"} {
		pattern, message := ulidPattern, "must be a canonical uppercase ULID"
		if field == "event_id" {
			pattern, message = uuidPattern, "must be a lowercase hyphenated UUID"
		}
		text, ok := root[field].(string)
		if !ok || !pattern.MatchString(text) {
			return invalid(field, "identifier", message)
		}
	}
	if d.Topic != "machinepulse/v1/telemetry/"+root["device_id"].(string) {
		return invalid("mqtt.topic", "device_mismatch", "must be machinepulse/v1/telemetry/{payload device_id}")
	}
	timestamp, ok := root["occurred_at"].(string)
	if !ok || !utcTimestamp(timestamp) {
		return invalid("occurred_at", "utc_timestamp", "must be an ISO date-time with seconds and an explicit UTC offset or Z")
	}
	if _, err := integer(root["sequence"], "sequence", false); err != nil {
		return err
	}
	sampling, err := object(root["sampling"], "sampling", "rate_hz", "sample_count", "window_duration_ms")
	if err != nil {
		return err
	}
	integers := make(map[string]*big.Int)
	for _, field := range []string{"rate_hz", "sample_count", "window_duration_ms"} {
		number, err := integer(sampling[field], "sampling."+field, true)
		if err != nil {
			return err
		}
		integers[field] = number
	}
	countDuration := new(big.Int).Mul(integers["sample_count"], big.NewInt(1000))
	rateDuration := new(big.Int).Mul(integers["rate_hz"], integers["window_duration_ms"])
	difference := new(big.Int).Sub(countDuration, rateDuration)
	if difference.Abs(difference).Cmp(big.NewInt(1000)) >= 0 {
		return invalid("sampling", "duration_mismatch", "sample count and duration must agree by less than one sample interval")
	}
	measurements, err := object(root["measurements"], "measurements", "temperature_c", "rpm", "vibration_m_s2")
	if err != nil {
		return err
	}
	temperature, err := finiteNumber(measurements["temperature_c"], "measurements.temperature_c")
	if err != nil {
		return err
	}
	if (policy.TemperatureMin != nil && temperature < *policy.TemperatureMin) || (policy.TemperatureMax != nil && temperature > *policy.TemperatureMax) {
		return invalid("measurements.temperature_c", "configured_bound", "outside configured inclusive temperature bounds")
	}
	rpm, err := finiteNumber(measurements["rpm"], "measurements.rpm")
	if err != nil {
		return err
	}
	if rpm < 0 {
		return invalid("measurements.rpm", "range", "must be non-negative")
	}
	axes, err := object(measurements["vibration_m_s2"], "measurements.vibration_m_s2", "x", "y", "z")
	if err != nil {
		return err
	}
	for _, axis := range []string{"x", "y", "z"} {
		path := "measurements.vibration_m_s2." + axis
		samples, ok := axes[axis].([]any)
		if !ok {
			return invalid(path, "type", "must be an array of finite numbers")
		}
		if integers["sample_count"].Cmp(big.NewInt(int64(len(samples)))) != 0 {
			return invalid(path, "sample_count", "array length must equal sampling.sample_count")
		}
		for i, sample := range samples {
			samplePath := fmt.Sprintf("%s[%d]", path, i)
			number, err := finiteNumber(sample, samplePath)
			if err != nil {
				return err
			}
			if policy.AccelerationMax != nil && math.Abs(number) > *policy.AccelerationMax {
				return invalid(samplePath, "configured_bound", "outside configured inclusive absolute acceleration bound")
			}
		}
	}
	return nil
}

func utcTimestamp(value string) bool {
	// ISO permits a space or lower-case separator; preserve original bytes.
	if len(value) > 10 && (value[10] == ' ' || value[10] == 't') {
		value = value[:10] + "T" + value[11:]
	}
	if strings.HasSuffix(value, "z") {
		value = strings.TrimSuffix(value, "z") + "Z"
	}
	timestamp, err := time.Parse(time.RFC3339Nano, value)
	if err != nil {
		return false
	}
	_, offset := timestamp.Zone()
	return offset == 0
}

func integer(value any, path string, positive bool) (*big.Int, *ValidationError) {
	number, ok := value.(json.Number)
	parsed, valid := new(big.Int).SetString(string(number), 10)
	if !ok || !valid || strings.ContainsAny(string(number), ".eE") || parsed.Sign() < 0 || (positive && parsed.Sign() == 0) {
		return nil, invalid(path, "integer", "must be a non-negative JSON integer (strictly positive for sampling)")
	}
	return parsed, nil
}

func finiteNumber(value any, path string) (float64, *ValidationError) {
	number, ok := value.(json.Number)
	parsed, err := number.Float64()
	if !ok || err != nil || math.IsNaN(parsed) || math.IsInf(parsed, 0) {
		return 0, invalid(path, "finite_number", "must be a finite JSON number")
	}
	return parsed, nil
}

func object(value any, path string, fields ...string) (map[string]any, *ValidationError) {
	result, ok := value.(map[string]any)
	if !ok {
		return nil, invalid(path, "type", "must be a JSON object")
	}
	for _, field := range fields {
		if _, exists := result[field]; !exists {
			return nil, invalid(path+"."+field, "required", "required field is missing")
		}
	}
	keys := make([]string, 0, len(result))
	for key := range result {
		keys = append(keys, key)
	}
	slices.Sort(keys)
	for _, key := range keys {
		if !slices.Contains(fields, key) {
			return nil, invalid(path+"."+key, "unknown_field", "undeclared field is unsupported")
		}
	}
	return result, nil
}

// readJSON detects ambiguous duplicate keys before encoding/json can discard
// them. Container depth is bounded independently of the inbound packet limit.
func readJSON(decoder *json.Decoder, path string, depth int) (any, *ValidationError) {
	token, err := decoder.Token()
	if err != nil {
		return nil, invalid(path, "invalid_json", "malformed or incomplete JSON")
	}
	delimiter, container := token.(json.Delim)
	if !container {
		return token, nil
	}
	if depth >= 64 {
		return nil, invalid(path, "nesting_limit", "JSON exceeds 64 nested containers")
	}
	var result any
	switch delimiter {
	case '{':
		fields := make(map[string]any)
		for decoder.More() {
			token, err := decoder.Token()
			key, ok := token.(string)
			if err != nil || !ok {
				return nil, invalid(path, "invalid_json", "expected object key")
			}
			if _, exists := fields[key]; exists {
				return nil, invalid(path+"."+key, "duplicate_key", "duplicate object key is unsupported")
			}
			value, reason := readJSON(decoder, path+"."+key, depth+1)
			if reason != nil {
				return nil, reason
			}
			fields[key] = value
		}
		result = fields
	case '[':
		values := make([]any, 0)
		for decoder.More() {
			value, err := readJSON(decoder, fmt.Sprintf("%s[%d]", path, len(values)), depth+1)
			if err != nil {
				return nil, err
			}
			values = append(values, value)
		}
		result = values
	default:
		return nil, invalid(path, "invalid_json", "unexpected container delimiter")
	}
	if _, err := decoder.Token(); err != nil {
		return nil, invalid(path, "invalid_json", "incomplete JSON container")
	}
	return result, nil
}
