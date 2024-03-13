# Terracotta docker

This directory contains the files to build the Terracotta docker image. This image can be used to serve the tile server.
It can also be used to connect to a running terracotta tiler and serve the client depending on the value of the environment variable `TERRACOTTA_SERVICE`. By default, the tiler server is started.

## Build the image

Build using the default image name and tag:
```bash
$ make build
```

Build using a custom registry, image name and tag:
```bash
$ make build REGISTRY=myregistry.com IMAGE=terracotta TAG=test
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

## Start the server (local database)

```bash
$ docker run -v /path/to/database:/mnt TERRACOTTA_SERVICE=tiler -e TC_DRIVER_PATH=/mnt/db.sqlite myregistry.com/terracotta:test
```

## Start the client

```bash
$ docker run -e TERRACOTTA_SERVICE=client -e TERRACOTTA_API_URL=<url to terracotta tiler> myregistry.com/terracotta:test
```
