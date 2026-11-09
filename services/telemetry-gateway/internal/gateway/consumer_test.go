package gateway

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/segmentio/kafka-go"
)

type consumerProbe struct {
	commits               int
	writes                int
	commitErr, errorWrite error
	letter                kafka.Message
}

func (p *consumerProbe) FetchMessage(context.Context) (kafka.Message, error) {
	return kafka.Message{}, errors.New("end")
}
func (p *consumerProbe) CommitMessages(context.Context, ...kafka.Message) error {
	p.commits++
	return p.commitErr
}
func (p *consumerProbe) WriteMessages(_ context.Context, m ...kafka.Message) error {
	p.writes++
	p.letter = m[0]
	return p.errorWrite
}
func consumerFixture(t *testing.T) kafka.Message {
	t.Helper()
	raw, err := os.ReadFile("testdata/internal.telemetry.v1.json")
	if err != nil {
		t.Fatal(err)
	}
	return kafka.Message{Topic: InternalTopic, Partition: 0, Offset: 7, Key: []byte("01M000000028T5CY4GNF6YY4HM"), Value: raw}
}
func TestConsumerDispositions(t *testing.T) {
	for _, tc := range []struct {
		name, terminal         string
		failures               int
		writeFail, commitFail  bool
		commits, writes, calls int
		wantErr                bool
	}{
		{"success", "stop", 0, false, false, 1, 0, 1, false},
		{"retry succeeds", "stop", 1, false, false, 1, 0, 2, false},
		{"stop exhausted", "stop", 9, false, false, 0, 0, 2, true},
		{"dead letter", "dead-letter", 9, false, false, 1, 1, 2, false},
		{"dead letter outage", "dead-letter", 9, true, false, 0, 1, 2, true},
		{"commit outage", "stop", 0, false, true, 1, 0, 1, true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			p := &consumerProbe{}
			if tc.writeFail {
				p.errorWrite = errors.New("sink unavailable")
			}
			if tc.commitFail {
				p.commitErr = errors.New("commit unavailable")
			}
			var logs bytes.Buffer
			calls := 0
			m := consumerFixture(t)
			err := consumeRecord(context.Background(), p, p, "test", ConsumerPolicy{2, time.Nanosecond, time.Second, tc.terminal}, slog.New(slog.NewJSONHandler(&logs, nil)), func(context.Context, InternalEvent) error {
				calls++
				if calls <= tc.failures {
					return errors.New("injected failure")
				}
				return nil
			}, m)
			if (err != nil) != tc.wantErr || p.commits != tc.commits || p.writes != tc.writes || calls != tc.calls {
				t.Fatalf("err=%v commits=%d writes=%d calls=%d", err, p.commits, p.writes, calls)
			}
			if p.writes > 0 {
				var letter DeadLetter
				if err := json.Unmarshal(p.letter.Value, &letter); err != nil {
					t.Fatal(err)
				}
				if !bytes.Equal(letter.Value, m.Value) || letter.Offset != 7 || letter.Attempts != 2 || letter.Reason != "injected failure" || letter.Group != "test" {
					t.Fatalf("lost provenance: %+v", letter)
				}
			}
			if calls > 1 && !strings.Contains(logs.String(), "consumer_attempt_failed") {
				t.Fatal("missing retry evidence")
			}
		})
	}
}
func TestConsumerCancellationAndDuplicates(t *testing.T) {
	p := &consumerProbe{}
	m := consumerFixture(t)
	var logs bytes.Buffer
	logger := slog.New(slog.NewJSONHandler(&logs, nil))
	policy := ConsumerPolicy{2, time.Hour, time.Second, "dead-letter"}
	ctx, cancel := context.WithCancel(context.Background())
	err := consumeRecord(ctx, p, p, "test", policy, logger, func(context.Context, InternalEvent) error { cancel(); return errors.New("failed") }, m)
	if !errors.Is(err, context.Canceled) || p.commits != 0 || p.writes != 0 {
		t.Fatalf("cancellation committed: %v", err)
	}
	for range 2 {
		if err := consumeRecord(context.Background(), p, p, "test", policy, logger, func(context.Context, InternalEvent) error { return nil }, m); err != nil {
			t.Fatal(err)
		}
	}
	if strings.Count(logs.String(), "consumer_disposition") != 2 || strings.Count(logs.String(), "550e8400-e29b-41d4-a716-446655440000") != 2 {
		t.Fatal("duplicate identities not observable")
	}
}
func TestConsumerRejectsInconsistentEnvelope(t *testing.T) {
	p := &consumerProbe{}
	m := consumerFixture(t)
	m.Key = []byte("wrong-device")
	called := false
	err := consumeRecord(context.Background(), p, p, "test", ConsumerPolicy{1, time.Second, time.Second, "dead-letter"}, slog.Default(), func(context.Context, InternalEvent) error { called = true; return nil }, m)
	if err != nil || called || p.writes != 1 || p.commits != 1 {
		t.Fatalf("invalid envelope disposition: %v", err)
	}
}

func TestConsumerAttemptTimeout(t *testing.T) {
	p := &consumerProbe{}
	calls := 0
	err := consumeRecord(context.Background(), p, p, "test", ConsumerPolicy{1, time.Second, time.Millisecond, "stop"}, slog.Default(), func(ctx context.Context, _ InternalEvent) error {
		calls++
		<-ctx.Done()
		return nil // A handler returning nil after expiry still must not commit.
	}, consumerFixture(t))
	if !errors.Is(err, context.DeadlineExceeded) || p.commits != 0 || calls != 1 {
		t.Fatalf("expired attempt committed: %v", err)
	}
}

func TestConsumerPolicyValidation(t *testing.T) {
	p := &consumerProbe{}
	err := RunConsumer(context.Background(), p, nil, "test", ConsumerPolicy{1, time.Second, time.Second, "dead-letter"}, slog.Default(), func(context.Context, InternalEvent) error { return nil })
	if err == nil {
		t.Fatal("accepted dead-letter policy without writer")
	}
}
