FROM continuumio/miniconda3

ENV PYTHONUTF8=1
ENV RUN_IN_DOCKER=1
WORKDIR /app
VOLUME [ "/data" ]

RUN apt-get update && \
    apt-get -qy full-upgrade && \
    apt-get install -qy curl

RUN curl -sSL https://get.docker.com/ | sh

COPY ./condarc /root/.condarc

RUN conda create -n main python=3.10 -qy

COPY ./requirements.txt /app/requirements.txt

RUN [ "conda", "run", "-n", "main", "--no-capture-output", "python", "-u", "-m", "pip", "install", "-r", "/app/requirements.txt" ]

COPY ./aexpy /app/aexpy

RUN [ "conda", "run", "-n", "main", "--no-capture-output", "python", "-u", "-m", "aexpy", "bat", "-s", "bas"]

ENTRYPOINT [ "conda", "run", "-n", "main", "--no-capture-output", "python", "-u", "-m", "aexpy", "-c", "/data" ]