IMAGE_NAME=ynput/ayon-ash
VERSION=$(shell python -c 'import ash; print(ash.__version__)')

default:
	@echo "Use make build to build $(IMAGE_NAME):$(VERSION)"

run:
	docker run \
		-it --rm \
		--hostname worker \
		-v $(shell pwd)/ash:/ash/ash \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-e AYON_API_KEY=veryinsecurapikey \
		-e AYON_SERVER_URL=http://localhost:5000 \
		--log-driver=syslog \
		--log-opt syslog-address=udp://localhost:514 \
		$(IMAGE_NAME):latest

build:
	docker build -t $(IMAGE_NAME):latest -t $(IMAGE_NAME):$(VERSION) .

dist: build
	docker push ynput/ayon-ash:$(VERSION)
	docker push ynput/ayon-ash:latest
