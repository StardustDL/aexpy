FROM node:16

WORKDIR /app/web

COPY ./src/web/package*.json /app/web/

RUN npm --registry=https://registry.npmmirror.com ci

COPY ./src/web /app/web

RUN npm run build

FROM continuumio/miniconda3

ENV PYTHONUTF8=1
ENV RUN_IN_DOCKER=1

ENV AEXPY_CACHE=/data
ENV AEXPY_CONFIG=/config/config.yml

WORKDIR /app
EXPOSE 8008
VOLUME [ "/data" ]









RUN conda create -n main python=3.10 -qy && \
    conda create -n py39 python=3.9 -qy && \
    conda create -n py38 python=3.8 -qy && \
    conda create -n py37 python=3.7 -qy

COPY ./src/requirements.txt /app/requirements.txt

RUN [ "conda", "run", "-n", "main", "--no-capture-output", "python", "-u", "-m", "pip", "install", "-r", "/app/requirements.txt" ]

COPY ./src/aexpy /app/aexpy

RUN [ "conda", "run", "-n", "main", "--no-capture-output", "python", "-u", "-m", "aexpy", "initialize"]

COPY --from=0 /app/web/dist /app/aexpy/serving/server/wwwroot

ARG GIT_COMMIT
ENV GIT_COMMIT=${GIT_COMMIT:-unknown}

ARG BUILD_DATE
ENV BUILD_DATE=${BUILD_DATE:-unknown}

ENTRYPOINT [ "conda", "run", "-n", "main", "--no-capture-output", "python", "-u", "-m", "aexpy" ]