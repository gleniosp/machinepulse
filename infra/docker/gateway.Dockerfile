FROM --platform=$BUILDPLATFORM golang:1.27.1-bookworm@sha256:8d48e12ec56735e9358640898b9d9b9fcca110612ed8a5567438c0a1baa24e66 AS build
WORKDIR /src
ENV GOWORK=off
COPY services/telemetry-gateway/go.mod services/telemetry-gateway/go.sum ./
RUN go mod download && go mod verify
COPY services/telemetry-gateway/cmd/ ./cmd/
COPY services/telemetry-gateway/internal/ ./internal/
ARG TARGETOS
ARG TARGETARCH
RUN CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH \
    go build -mod=readonly -trimpath -ldflags="-s -w" \
    -o /out/telemetry-gateway ./cmd/telemetry-gateway
RUN mkdir -p /out/quarantine && chown 65532:65532 /out/quarantine && chmod 700 /out/quarantine

FROM scratch AS runtime
COPY --from=build /out/telemetry-gateway /telemetry-gateway
COPY LICENSE /licenses/MachinePulse-LICENSE
COPY --from=build --chown=65532:65532 /out/quarantine /var/lib/machinepulse/quarantine
ENV MACHINEPULSE_GATEWAY_QUARANTINE_DIR=/var/lib/machinepulse/quarantine
USER 65532:65532
ENTRYPOINT ["/telemetry-gateway"]
