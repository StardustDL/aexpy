FROM continuumio/miniconda3

ENV PYTHONUTF8=1

WORKDIR /app
VOLUME [ "/data" ]

RUN conda create -n main python=3.12 -qy

COPY ./pyproject.toml /app/pyproject.toml

RUN [ "conda", "run", "-n", "main", "--no-capture-output", "python", "-u", "-m", "pip", "install", "-r", "/app/pyproject.toml" ]

COPY ./src/aexpy /app/aexpy

ARG GIT_COMMIT
ENV GIT_COMMIT=${GIT_COMMIT:-unknown}

ARG BUILD_DATE
ENV BUILD_DATE=${BUILD_DATE:-unknown}

ENTRYPOINT [ "conda", "run", "-n", "main", "--no-capture-output", "python", "-u", "-m", "aexpy" ]