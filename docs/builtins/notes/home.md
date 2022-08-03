---
name: home
creation: 2022-05-09 18:55:36.271649+08:00
modification: 2022-05-09 18:55:36.271649+08:00
targets: {}
tags: []
extra: {}
schema: ''
---

# AexPy

> This website is for a paper's related information for now. Copying and referencing by others are not allowed at now.
> Accessing this website from China may need VPN because of resource files from jsDelivr CDN service.

AexPy */eɪkspaɪ/* is an **A**pi **EX**plorer in **PY**thon. It is a tool for API breaking change detection in Python packages.

This page describes how to get and use AexPy. We provide the experiment data at [Data](/data), and the full change patterns are given at [Change Specification](/change-spec).

## Download

We provide a docker image for AexPy. You can pull the image via the following scripts.

```sh
docker pull registry.us-west-1.aliyuncs.com/aexpy/aexpy:latest

# use a short tag name for convenience
docker tag registry.us-west-1.aliyuncs.com/aexpy/aexpy:latest aexpy:latest
```

## Usage

Use the following command to see the help screen for command-line commands and options.

```sh
docker run aexpy:latest --help
```

### Extract API & Detect Changes

Use the following command to detect changes between v1.0 and v2.0 of a package named demo:

```sh
docker run aexpy:latest report demo@1.0:2.0

# e.g. detect API changes between jinja2 v3.1.1 and v3.1.2
docker run aexpy:latest report jinja2@3.1.1:3.1.2
```

Use the following command to extract API information of v1.0 of a package named demo:

```sh
docker run aexpy:latest extract demo@1.0

# e.g. extract APIs from click v8.1.3
docker run aexpy:latest extract click@8.1.3
```

### View Processing Logs

The processing may cost time, you can use multiple `-v` for verbose logs.

```sh
docker run aexpy:latest -vvv extract click@8.1.3
```

### Store Raw Data

You can mount cache directory to `/data` to save the processed data. AexPy will use the cache data if it exists, and produce results in JSON format under the cache directory.

```sh
docker run -v /path/to/cache:/data aexpy:latest extract click@8.1.3

cat /path/to/cache/extracting/types/click/8.1.3.json
```
