# static configuration data
COMMIT := $(shell git rev-parse --short=8 HEAD)
DOCKER_IMAGE := fidays/airline-engine-scraper:$(COMMIT)
NAMESPACE := airline-engine
APP := $(shell echo $(DOCKER_IMAGE) | sed -E 's|^.*/(.+):.*$$|\1|')



# build docker image
build:
	docker build  -t $(DOCKER_IMAGE) -f Dockerfile .


# run and execute into the container
exec:
	docker run \
	--rm \
	-it \
	$(DOCKER_IMAGE) /bin/sh


# run docker container
run:
	docker run \
	--rm \
	-it \
	--env-file .env \
	$(DOCKER_IMAGE)


# push docker image to dockerhub
push:
	docker push $(DOCKER_IMAGE)



%:
	@:

.PHONY: build exec run