FROM node:16

WORKDIR /app/web

COPY ./src/web/package*.json /app/web/

RUN npm ci

COPY ./src/web /app/web

RUN npm run build

FROM continuumio/miniconda3

ENV PYTHONUTF8=1
ENV RUN_IN_DOCKER=1
ENV AEXPY_CACHE=/data
ENV AEXPY_CONFIG=/config/config.yml

WORKDIR /app
VOLUME [ "/data" ]

RUN apt-get update && \
    apt-get -qy full-upgrade && \
    apt-get install -qy curl

RUN curl -sSL https://get.docker.com/ | sh

COPY ./docker/condarc /root/.condarc

RUN conda create -n main python=3.10 -qy && \
    conda create -n py39 python=3.9 -qy && \
    conda create -n py38 python=3.8 -qy && \
    conda create -n py37 python=3.7 -qy

COPY ./src/requirements.txt /app/requirements.txt

RUN [ "conda", "run", "-n", "main", "--no-capture-output", "python", "-u", "-m", "pip", "install", "-r", "/app/requirements.txt" ]

COPY ./src/aexpy /app/aexpy

COPY --from=0 /app/web/dist /app/aexpy/serving/server/wwwroot

RUN [ "conda", "run", "-n", "main", "--no-capture-output", "python", "-u", "-m", "aexpy", "rebuild"]

ENTRYPOINT [ "conda", "run", "-n", "main", "--no-capture-output", "python", "-u", "-m", "aexpy" ]