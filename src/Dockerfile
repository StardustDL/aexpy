FROM continuumio/anaconda3

RUN conda install python=3.10

RUN apt-get update && \
    apt-get -qy full-upgrade && \
    apt-get install -qy curl

RUN curl -sSL https://get.docker.com/ | sh

ENV PYTHONUTF8=1
ENV RUN_IN_DOCKER=1

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

VOLUME [ "/data" ]

RUN [ "python", "-m", "pip", "install", "-r", "/app/requirements.txt" ]

COPY ./aexpy /app/aexpy

RUN [ "python", "-m", "aexpy", "bat", "-s", "bas"]

ENTRYPOINT [ "python", "-u", "-m", "aexpy", "-c", "/data" ]