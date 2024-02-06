FROM mambaorg/micromamba:latest

ARG MAMBA_DOCKERFILE_ACTIVATE=1
ENV PYTHONUTF8=1
ENV RUN_IN_DOCKER=1
ENV AEXPY_ENV_PROVIDER=micromamba
ARG GIT_COMMIT
ENV GIT_COMMIT=${GIT_COMMIT:-unknown}
ARG BUILD_DATE
ENV BUILD_DATE=${BUILD_DATE:-unknown}

WORKDIR /app
VOLUME [ "/data" ]

COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml
RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes

COPY --chown=$MAMBA_USER:$MAMBA_USER ./src/aexpy /app/aexpy

ENTRYPOINT [ "/usr/local/bin/_entrypoint.sh", "python", "-u", "-m", "aexpy" ]