package main

import (
	"context"
	"errors"
	"flag"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/gleniosp/machinepulse/services/telemetry-gateway/internal/gateway"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stderr, nil))
	config, err := parseConfig(os.Args[1:], os.LookupEnv, os.Stderr)
	if errors.Is(err, flag.ErrHelp) {
		return
	}
	if err != nil {
		logger.Error("gateway_configuration_failed", "error", err)
		os.Exit(2)
	}
	publisher := gateway.NewStreamPublisher(config.KafkaAddress, config.OperationTimeout)
	defer func() {
		if err := publisher.Close(); err != nil {
			logger.Error("stream_close_failed", "error", err)
		}
	}()
	g, err := gateway.New(config, logger, publisher.Publish)
	if err != nil {
		logger.Error("gateway_configuration_failed", "error", err)
		os.Exit(2)
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	logger.Info("gateway_stream_mode", "topic", gateway.InternalTopic, "kafka", config.KafkaAddress)
	if err := g.Run(ctx); err != nil {
		logger.Error("gateway_failed", "error", err)
		os.Exit(1)
	}
}
