package gateway

import (
	"fmt"
	"io"
	"net"
	"sync"
)

// packetLimitConn checks MQTT frame lengths before Paho sees the header and
// allocates the frame body. Paho v0.23.0 only advertises MaximumPacketSize.
// Close and deadline methods remain available while Read is blocked.
type packetLimitConn struct {
	net.Conn
	mu     sync.Mutex
	reader packetReader
}

func limitPackets(conn net.Conn, maximum uint32) *packetLimitConn {
	return &packetLimitConn{Conn: conn, reader: packetReader{source: conn, maximum: maximum}}
}

func (c *packetLimitConn) Read(p []byte) (int, error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.reader.Read(p)
}

// packetReader holds only the fixed header (at most five bytes). It streams
// each permitted body directly and checks every subsequent frame separately.
type packetReader struct {
	source     io.Reader
	maximum    uint32
	header     [5]byte
	headerSize int
	headerRead int
	remaining  uint32
}

func (r *packetReader) Read(p []byte) (int, error) {
	if len(p) == 0 {
		return 0, nil
	}
	if r.headerRead == r.headerSize && r.remaining == 0 {
		if err := r.readHeader(); err != nil {
			return 0, err
		}
	}
	if r.headerRead < r.headerSize {
		n := copy(p, r.header[r.headerRead:r.headerSize])
		r.headerRead += n
		return n, nil
	}
	n, err := r.source.Read(p[:min(len(p), int(r.remaining))])
	r.remaining -= uint32(n)
	return n, err
}

func (r *packetReader) readHeader() error {
	if _, err := io.ReadFull(r.source, r.header[:1]); err != nil {
		return err
	}
	var remaining uint32
	for i := 1; i < len(r.header); i++ {
		if _, err := io.ReadFull(r.source, r.header[i:i+1]); err != nil {
			return err
		}
		b := r.header[i]
		remaining |= uint32(b&0x7f) << (7 * (i - 1))
		if b&0x80 != 0 {
			continue
		}
		size := uint64(i+1) + uint64(remaining)
		if size > uint64(r.maximum) {
			return fmt.Errorf("MQTT packet size %d exceeds configured maximum %d", size, r.maximum)
		}
		r.headerSize, r.headerRead, r.remaining = i+1, 0, remaining
		return nil
	}
	return fmt.Errorf("MQTT remaining length exceeds four bytes")
}
