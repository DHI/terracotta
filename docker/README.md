# Terracotta docker

This directory contains the docker files to build the Terracotta docker image.

## Build the image
**Make sure the current directory is in docker/**

Build using the default image name and tag:
```bash
make build
```

Build using a custom registry, image name and tag:
```bash
make build REGISTRY=myregistry.com IMAGE=terracotta TAG=test
```

## Push the image
**Make sure the current directory is in docker/**

Push using the default image name and tag:
```bash
make push
```

Push using a custom registry, image name and tag:
```bash
make push REGISTRY=myregistry.com IMAGE=terracotta TAG=test
```
