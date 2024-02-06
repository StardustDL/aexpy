FROM mambaorg/micromamba:latest

ENV PYTHONUTF8=1
ENV RUN_IN_DOCKER=1

WORKDIR /app
VOLUME [ "/data" ]

RUN micromamba create -n main python=3.12 -c conda-forge -qy

COPY ./requirements.txt /app/requirements.txt

RUN [ "micromamba", "run", "-n", "main", "python", "-u", "-m", "pip", "install", "-r", "/app/requirements.txt" ]

COPY ./src/aexpy /app/aexpy

ARG GIT_COMMIT
ENV GIT_COMMIT=${GIT_COMMIT:-unknown}

ARG BUILD_DATE
ENV BUILD_DATE=${BUILD_DATE:-unknown}

ENTRYPOINT [ "micromamba", "run", "-n", "main", "python", "-u", "-m", "aexpy" ]