package gateway

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/eclipse/paho.golang/paho"
)

func sourcePacket() *paho.Publish {
	return &paho.Publish{Topic: sourceTopic, QoS: 1, Payload: []byte(sourceJSON)}
}

type quarantineFunc func(context.Context, Rejection) error

func (f quarantineFunc) Store(ctx context.Context, r Rejection) error { return f(ctx, r) }

func readQuarantine(t *testing.T, directory string) []Rejection {
	t.Helper()
	paths, err := filepath.Glob(filepath.Join(directory, "*.json"))
	if err != nil {
		t.Fatal(err)
	}
	var records []Rejection
	for _, path := range paths {
		payload, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		var record Rejection
		if err := json.Unmarshal(payload, &record); err != nil {
			t.Fatal(err)
		}
		records = append(records, record)
		info, err := os.Stat(path)
		if err != nil || info.Mode().Perm() != 0600 {
			t.Fatalf("quarantine file permissions: %v, %v", info, err)
		}
	}
	return records
}

func TestQuarantinePersistsExactArbitraryBytesAcrossReopen(t *testing.T) {
	directory := filepath.Join(t.TempDir(), "parent", "quarantine")
	q, err := newFileQuarantine(directory)
	if err != nil {
		t.Fatal(err)
	}
	payload := []byte{'{', 0xff, 0, '\n', '}'}
	delivery := deliveryFor(sourceTopic, payload, time.Now())
	record := rejection(delivery, 1, false, invalid("payload", "invalid_json", "malformed JSON"))
	for range 2 {
		if err := q.Store(context.Background(), record); err != nil {
			t.Fatal(err)
		}
	}
	// A new process instance needs no in-memory index to recover completed data.
	if _, err := newFileQuarantine(directory); err != nil {
		t.Fatal(err)
	}
	records := readQuarantine(t, directory)
	if len(records) != 2 {
		t.Fatalf("retry records overwritten: %d", len(records))
	}
	digest := sha256.Sum256(payload)
	for _, got := range records {
		if !bytes.Equal(got.Payload, payload) || got.PayloadSHA256 != hex.EncodeToString(digest[:]) ||
			got.Topic != sourceTopic || got.QoS != 1 || got.Retained || got.Version != "quarantine.v1" ||
			!got.GatewayReceivedAt.Equal(delivery.GatewayReceivedAt) || got.Reason.Code != "invalid_json" {
			t.Fatalf("record lost source/reason: %+v", got)
		}
	}
	pending, err := filepath.Glob(filepath.Join(directory, ".pending-*"))
	if err != nil || len(pending) != 0 {
		t.Fatalf("unpublished temporary files: %v, %v", pending, err)
	}
}

func TestCancelledQuarantineDoesNotPublish(t *testing.T) {
	directory := t.TempDir()
	q, err := newFileQuarantine(directory)
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if err := q.Store(ctx, Rejection{}); !errors.Is(err, context.Canceled) {
		t.Fatalf("expected cancellation, got %v", err)
	}
	if len(readQuarantine(t, directory)) != 0 {
		t.Fatal("cancelled operation published a record")
	}
}

func TestQuarantineDirectoryMustBeUsable(t *testing.T) {
	path := filepath.Join(t.TempDir(), "file")
	if err := os.WriteFile(path, []byte("occupied"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := newFileQuarantine(path); err == nil {
		t.Fatal("regular file accepted as quarantine directory")
	}
	q := &fileQuarantine{directory: filepath.Join(t.TempDir(), "missing")}
	if err := q.Store(context.Background(), Rejection{}); err == nil {
		t.Fatal("missing directory write succeeded")
	}
}

func TestInvalidPayloadIsPersistedBeforeAckWithRecoverableIdentity(t *testing.T) {
	var logs bytes.Buffer
	g := testGateway(t, func(context.Context, Delivery) error { t.Fatal("invalid payload reached valid handler"); return nil }, &logs)
	packet := sourcePacket()
	packet.Payload = []byte(strings.Replace(sourceJSON, `"sequence":9007199254740993`, `"sequence":null`, 1))
	if err := g.receive(context.Background(), packet, func(*paho.Publish) error {
		records := readQuarantine(t, g.config.QuarantineDir)
		if len(records) != 1 || !bytes.Equal(records[0].Payload, packet.Payload) || records[0].Source.EventID == "" || records[0].Reason.Path != "sequence" {
			t.Fatalf("ack before complete quarantine record: %+v", records)
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if c := g.Counters(); c != (ValidationCounters{Received: 1, Invalid: 1, Quarantined: 1}) {
		t.Fatalf("unexpected counters: %+v", c)
	}
	for _, event := range []string{"telemetry_rejected", "telemetry_quarantined", "telemetry_disposition_complete", "telemetry_validation_counters"} {
		if !strings.Contains(logs.String(), event) {
			t.Errorf("missing %s", event)
		}
	}
}

func TestQuarantineFailureAndDeadlineNeverAcknowledge(t *testing.T) {
	for _, mode := range []string{"storage failure", "cancellation", "expired success"} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			g := testGateway(t, func(context.Context, Delivery) error { t.Fatal("valid handler called"); return nil }, io.Discard)
			g.quarantine = quarantineFunc(func(context.Context, Rejection) error {
				if mode == "storage failure" {
					return errors.New("directory sync failed")
				}
				cancel()
				if mode == "cancellation" {
					return context.Canceled
				}
				return nil
			})
			packet := sourcePacket()
			packet.Payload = []byte("{")
			if err := g.receive(ctx, packet, func(*paho.Publish) error { t.Fatal("ack on failed disposition"); return nil }); err == nil {
				t.Fatal("expected failure")
			}
			if c := g.Counters(); c.Invalid != 1 || c.QuarantineFailed != 1 || c.Quarantined != 0 {
				t.Fatalf("unexpected counters: %+v", c)
			}
		})
	}
}

func TestAckFailureRetainsQuarantineRecord(t *testing.T) {
	g := testGateway(t, func(context.Context, Delivery) error { return nil }, io.Discard)
	packet := sourcePacket()
	packet.Payload = []byte("{")
	want := errors.New("connection lost before ack")
	if err := g.receive(context.Background(), packet, func(*paho.Publish) error { return want }); !errors.Is(err, want) {
		t.Fatal(err)
	}
	if len(readQuarantine(t, g.config.QuarantineDir)) != 1 || g.Counters().Quarantined != 1 {
		t.Fatal("ack failure lost durable rejection")
	}
}

func TestSourceIndexRetainsOtherStringsWhenOneFieldHasWrongType(t *testing.T) {
	delivery := deliveryFor(sourceTopic, []byte(strings.Replace(sourceJSON, `"event_id":"09f5ca55-ec6a-50cb-9dc0-caa53d0d4171"`, `"event_id":12`, 1)), time.Now())
	if delivery.Source.EventID != "" || delivery.Source.DeviceID == "" || delivery.Source.OccurredAt == "" {
		t.Fatalf("best-effort source lost: %+v", delivery.Source)
	}
}
