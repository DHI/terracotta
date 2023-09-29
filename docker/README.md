# Terracotta docker

This directory contains the files to build the Terracotta docker image.

## Build the image

Build using the default image name and tag:
```bash
$ make build
```

Build using a custom registry, image name and tag:
```bash
$ make build REGISTRY=myregistry.com IMAGE=terracotta TAG=test
```

## Start the server (locally)

```bash
$ docker run -v /path/to/database:/mnt -e TC_DRIVER_PATH=/mnt/db.sqlite -t myregistry.com/terracotta:test
```

## Push the image to a registry

Push using the default image name and tag:
```bash
$ make push
```

Push using a custom registry, image name and tag:
```bash
$ make push REGISTRY=myregistry.com IMAGE=terracotta TAG=test
```
