FROM python:latest as BUILD
RUN pip install build
COPY . /src
RUN python -m build /src --outdir /dist

FROM mambaorg/micromamba:latest

ARG MAMBA_DOCKERFILE_ACTIVATE=1
ENV PYTHONUTF8=1
ENV RUN_IN_CONTAINER=1
ENV AEXPY_ENV_PROVIDER=micromamba

WORKDIR /app
VOLUME [ "/data" ]

COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml
RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes

COPY --from=BUILD --chown=$MAMBA_USER:$MAMBA_USER /dist /tmp/packages

RUN pip install --no-cache-dir /tmp/packages/*.whl && \
    rm -rf /tmp/packages

ENTRYPOINT [ "/usr/local/bin/_entrypoint.sh", "aexpy" ]