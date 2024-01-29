FROM continuumio/miniconda3

ENV PYTHONUTF8=1
ENV RUN_IN_DOCKER=1

WORKDIR /app
VOLUME [ "/data" ]

RUN conda create -n main python=3.12 -qy

COPY ./requirements.txt /app/requirements.txt

RUN [ "conda", "run", "-n", "main", "--no-capture-output", "python", "-u", "-m", "pip", "install", "-r", "/app/requirements.txt" ]

COPY ./src/aexpy /app/aexpy

ARG GIT_COMMIT
ENV GIT_COMMIT=${GIT_COMMIT:-unknown}

ARG BUILD_DATE
ENV BUILD_DATE=${BUILD_DATE:-unknown}

ENTRYPOINT [ "conda", "run", "-n", "main", "--no-capture-output", "python", "-u", "-m", "aexpy" ]