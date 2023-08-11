IMAGE=terracotta
VERSION=<>

all: build push

build:
	docker build -f ./docker/Dockerfile -t $(IMAGE):$(VERSION) .

push:
	docker push $(IMAGE):$(VERSION)

.PHONY: build push all
