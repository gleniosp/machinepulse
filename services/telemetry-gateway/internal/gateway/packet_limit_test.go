package gateway

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"strings"
	"testing"
	"testing/iotest"
	"time"

	"github.com/eclipse/paho.golang/packets"
)

func TestPacketLimitStreamsMultipleFramesAndFragmentedHeaders(t *testing.T) {
	// One two-byte control packet, a frame with a two-byte remaining length,
	// and another control packet. The limit applies to each individual frame.
	wire := append([]byte{0xd0, 0, 0x30, 0x80, 1}, bytes.Repeat([]byte{'x'}, 128)...)
	wire = append(wire, 0xd0, 0)
	for _, chunk := range []int{1, 2, 512} {
		t.Run(fmt.Sprint(chunk), func(t *testing.T) {
			r := &packetReader{source: iotest.OneByteReader(bytes.NewReader(wire)), maximum: 131}
			if n, err := r.Read(nil); n != 0 || err != nil {
				t.Fatalf("empty read: %d, %v", n, err)
			}
			var got bytes.Buffer
			buffer := make([]byte, chunk)
			for {
				n, err := r.Read(buffer)
				got.Write(buffer[:n])
				if errors.Is(err, io.EOF) {
					break
				}
				if err != nil {
					t.Fatal(err)
				}
			}
			if !bytes.Equal(got.Bytes(), wire) {
				t.Fatalf("wire bytes changed: %x", got.Bytes())
			}
		})
	}
}

func TestPacketLimitRejectsOversizeBeforeExposingHeaderOrReadingBody(t *testing.T) {
	body := bytes.Repeat([]byte{'x'}, 128)
	source := bytes.NewReader(append([]byte{0x30, 0x80, 1}, body...))
	r := &packetReader{source: source, maximum: 130} // Actual frame is 131 bytes.
	buffer := make([]byte, 512)
	n, err := r.Read(buffer)
	if n != 0 || err == nil || !strings.Contains(err.Error(), "exceeds configured maximum") {
		t.Fatalf("oversized header exposed: %d, %v", n, err)
	}
	if source.Len() != len(body) {
		t.Fatal("oversized body was read")
	}
}

func TestPacketLimitRejectsTruncatedAndInvalidLengths(t *testing.T) {
	for _, wire := range [][]byte{
		{0x30}, {0x30, 0x80}, {0x30, 0x80, 0x80, 0x80, 0x80}, {0x30, 2, 'x'},
	} {
		r := &packetReader{source: bytes.NewReader(wire), maximum: 1024}
		if _, err := packets.ReadPacket(r); err == nil {
			t.Fatalf("invalid frame accepted: %x", wire)
		}
	}
}

func TestConnectionRejectsOversizedConnackWithoutWaitingForBody(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	serverDone := make(chan error, 1)
	go func() {
		conn, err := listener.Accept()
		if err != nil {
			serverDone <- err
			return
		}
		defer conn.Close()
		_ = conn.SetDeadline(time.Now().Add(3 * time.Second))
		if _, err := packets.ReadPacket(conn); err != nil {
			serverDone <- err
			return
		}
		// Claim a body larger than the configured limit, but never send it.
		// The gateway must reject the header instead of waiting to fill it.
		if _, err := conn.Write([]byte{0x20, 64}); err != nil {
			serverDone <- err
			return
		}
		_, err = conn.Read(make([]byte, 1))
		if errors.Is(err, io.EOF) {
			err = nil
		}
		serverDone <- err
	}()
	g := testGateway(t, func(context.Context, Delivery) error { return nil }, io.Discard)
	g.config.BrokerAddress = listener.Addr().String()
	g.config.MaximumPacketSize = 32
	g.config.OperationTimeout = 2 * time.Second
	_, err = g.connect(context.Background())
	if err == nil || !strings.Contains(err.Error(), "exceeds configured maximum") {
		t.Fatalf("expected packet limit failure, got %v", err)
	}
	select {
	case err := <-serverDone:
		if err != nil {
			t.Fatal(err)
		}
	case <-time.After(4 * time.Second):
		t.Fatal("protocol server did not stop")
	}
}
