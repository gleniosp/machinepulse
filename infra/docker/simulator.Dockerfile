FROM ghcr.io/prefix-dev/pixi:0.83.0@sha256:3dce86c6e87371c58035aa41b09f2b56ca8f011722320551e0c2bfc1c59da5fb AS build
WORKDIR /app
COPY pixi.toml pixi.lock ./
COPY tools/simulator/pyproject.toml tools/simulator/pyproject.toml
COPY tools/simulator/src/ tools/simulator/src/
RUN pixi install --locked --environment default

FROM ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac AS runtime
# Conda prefixes and the editable package source must retain their build paths.
COPY --from=build /app/.pixi/envs/default/ /app/.pixi/envs/default/
COPY --from=build /app/tools/simulator/pyproject.toml /app/tools/simulator/pyproject.toml
COPY --from=build /app/tools/simulator/src/ /app/tools/simulator/src/
COPY tools/simulator/examples/ /app/tools/simulator/examples/
COPY pixi.toml pixi.lock /app/
COPY LICENSE /licenses/MachinePulse-LICENSE
ARG MACHINEPULSE_CODE_REVISION=""
ENV MACHINEPULSE_CODE_REVISION=$MACHINEPULSE_CODE_REVISION \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /output
USER 65532:65532
ENTRYPOINT ["/app/.pixi/envs/default/bin/python", "-m", "machinepulse_simulator.cli"]
CMD ["generate", "--config", "/app/tools/simulator/examples/runs.v1.json"]
