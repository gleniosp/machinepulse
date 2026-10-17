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
	g, err := gateway.New(config, logger, func(context.Context, gateway.Delivery) error {
		return gateway.ErrNoDisposition
	})
	if err != nil {
		logger.Error("gateway_configuration_failed", "error", err)
		os.Exit(2)
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	logger.Warn("gateway_observe_mode", "detail", "durable sinks are pending; deliveries remain unacknowledged and apply backpressure")
	if err := g.Run(ctx); err != nil {
		logger.Error("gateway_failed", "error", err)
		os.Exit(1)
	}
}
