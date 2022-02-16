FROM continuumio/anaconda3

RUN conda install python=3.10

RUN apt-get update && \
    apt-get -qy full-upgrade && \
    apt-get install -qy curl

RUN curl -sSL https://get.docker.com/ | sh

ENV PYTHONUTF8=1

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN [ "python", "-m", "pip", "install", "-r", "/app/requirements.txt" ]

COPY ./aexpy /app/aexpy
COPY ./third /app/third
COPY ./batch /app/batch

ENTRYPOINT [ "python", "-u", "-m" ]