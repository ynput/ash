IMAGE_NAME=ynput/ayon-ash
VERSION=$(shell python -c "import ash.version; print(ash.version.__version__, end='')")

run: build
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

check:
	uv version $(VERSION)
	uv run ruff check ash --fix
	uv run ruff format ash
	uv run mypy ash

build: check
	docker build -t $(IMAGE_NAME):latest -t $(IMAGE_NAME):$(VERSION) .

dist: build
	git checkout main && git pull && git merge develop && git push
	git tag -a $(VERSION) -m "Version $(VERSION)" && git push --tags

	gh release create \
		$(VERSION) \
		-t $(VERSION) \
		--generate-notes

	docker push ynput/ayon-ash:$(VERSION)
	docker push ynput/ayon-ash:latest
