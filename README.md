# AexPy

[AexPy](https://aexpy.netlify.app) */eɪkspaɪ/* is an **A**pi **EX**plorer in **PY**thon for detecting API breaking changes in packages.

## Prepare

### Normal Setup

```sh
docker --version
conda --version

# Build base environment for AexPy, PyCompat, and images for Pidiff.
aexpy prepare
```

### Docker Images

```sh
docker run aexpy/aexpy --help

# For cache, mount to /data
docker run -v /path/to/cache:/data aexpy/aexpy --help

# For pidiff, it need Docker in Docker, so we need to build the pidiff image outside docker container first.
aexpy prepare
docker run -v /var/run/docker.sock:/var/run/docker.sock run aexpy/aexpy --help
```

## Stages

### Preprocessing

```sh
aexpy preprocess coxbuild@0.0.1
```

### Extracting

```sh
aexpy extract coxbuild@0.0.1
```

### Differing

```sh
aexpy diff coxbuild@0.0.1:0.0.2
```

### Evaluating

```sh
aexpy evaluate coxbuild@0.0.1:0.0.2
```

### Reporting

```sh
aexpy report coxbuild@0.0.1:0.0.2
```

### Batching

```sh
aexpy batch coxbuild
```

## Development

### Restore

```sh
pip install coxbuild

cb restore

# Default running cache
mkdir ../aexpy-exps
```

### Run

```sh
cb run -- --help
```
