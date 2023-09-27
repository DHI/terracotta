REGISTRY=docker.io
IMAGE=terracotta
TAG=latest

all: build push

build:
	docker build -f Dockerfile -t $(REGISTRY)/$(IMAGE):$(TAG) ..

push:
	docker push $(REGISTRY)/$(IMAGE):$(TAG)

.PHONY: build push all
