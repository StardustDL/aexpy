FROM python:3.9

RUN apt-get update && \
    apt-get -qy full-upgrade && \
    apt-get install -qy curl

RUN curl -sSL https://get.docker.com/ | sh

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN [ "pip", "install", "-r", "/app/requirements.txt" ]

COPY ./aexpy /app/aexpy

ENTRYPOINT [ "python", "-u", "-m", "aexpy.test" ]