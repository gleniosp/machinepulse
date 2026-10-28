package gateway

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Rejection preserves arbitrary payload bytes, including invalid JSON/UTF-8.
// []byte is encoded as base64 by encoding/json. Source fields are untrusted.
type Rejection struct {
	Version           string           `json:"schema_version"`
	Source            Source           `json:"source"`
	Payload           []byte           `json:"payload_base64"`
	PayloadSHA256     string           `json:"payload_sha256"`
	Topic             string           `json:"mqtt_topic"`
	QoS               byte             `json:"mqtt_qos"`
	Retained          bool             `json:"mqtt_retained"`
	GatewayReceivedAt time.Time        `json:"gateway_received_at"`
	Reason            *ValidationError `json:"reason"`
}

func rejection(d Delivery, qos byte, retained bool, reason *ValidationError) Rejection {
	digest := sha256.Sum256(d.Payload)
	return Rejection{
		Version: "quarantine.v1", Source: d.Source, Payload: d.Payload,
		PayloadSHA256: hex.EncodeToString(digest[:]), Topic: d.Topic,
		QoS: qos, Retained: retained, GatewayReceivedAt: d.GatewayReceivedAt, Reason: reason,
	}
}

type quarantineSink interface {
	Store(context.Context, Rejection) error
}

// fileQuarantine commits one record at a time. A filename never uses producer
// input, and an incomplete write never appears as a completed .json record.
type fileQuarantine struct{ directory string }

func newFileQuarantine(directory string) (*fileQuarantine, error) {
	absolute, err := filepath.Abs(directory)
	if err != nil {
		return nil, err
	}
	if err := ensureDirectory(absolute); err != nil {
		return nil, fmt.Errorf("quarantine directory: %w", err)
	}
	return &fileQuarantine{directory: absolute}, nil
}

func ensureDirectory(path string) error {
	info, err := os.Stat(path)
	if err == nil {
		if !info.IsDir() {
			return fmt.Errorf("%s is not a directory", path)
		}
		return syncDirectory(path)
	}
	if !os.IsNotExist(err) {
		return err
	}
	parent := filepath.Dir(path)
	if err := ensureDirectory(parent); err != nil {
		return err
	}
	if err := os.Mkdir(path, 0700); err != nil && !os.IsExist(err) {
		return err
	}
	if err := syncDirectory(parent); err != nil {
		return err
	}
	return syncDirectory(path)
}

func syncDirectory(path string) error {
	directory, err := os.Open(path)
	if err != nil {
		return err
	}
	err = directory.Sync()
	closeErr := directory.Close()
	if err != nil {
		return err
	}
	return closeErr
}

func (q *fileQuarantine) Store(ctx context.Context, record Rejection) (storeErr error) {
	if err := ctx.Err(); err != nil {
		return err
	}
	file, err := os.CreateTemp(q.directory, ".pending-")
	if err != nil {
		return fmt.Errorf("create quarantine record: %w", err)
	}
	open, temporary := true, true
	// Preserve the primary failure as well as cleanup failures. Only this
	// operation's temporary file is removed; completed records are retained.
	defer func() {
		if open {
			if err := file.Close(); err != nil {
				storeErr = errors.Join(storeErr, fmt.Errorf("close incomplete quarantine record: %w", err))
			}
		}
		if temporary {
			if err := os.Remove(file.Name()); err != nil && !errors.Is(err, os.ErrNotExist) {
				storeErr = errors.Join(storeErr, fmt.Errorf("remove temporary quarantine record: %w", err))
			}
		}
	}()
	if err := json.NewEncoder(file).Encode(record); err != nil {
		return fmt.Errorf("write quarantine record: %w", err)
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	if err := file.Sync(); err != nil {
		return fmt.Errorf("sync quarantine record: %w", err)
	}
	open = false // Close consumes the file even when it reports an error.
	if err := file.Close(); err != nil {
		return fmt.Errorf("close quarantine record: %w", err)
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	name := strings.TrimPrefix(filepath.Base(file.Name()), ".pending-") + ".json"
	// Link publishes atomically and fails if a completed filename already
	// exists. It cannot overwrite an older record, even after a name collision.
	if err := os.Link(file.Name(), filepath.Join(q.directory, name)); err != nil {
		return fmt.Errorf("publish quarantine record: %w", err)
	}
	if err := os.Remove(file.Name()); err != nil {
		return fmt.Errorf("remove temporary quarantine record: %w", err)
	}
	temporary = false
	if err := syncDirectory(q.directory); err != nil {
		return fmt.Errorf("sync quarantine directory: %w", err)
	}
	return ctx.Err()
}
