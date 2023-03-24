default:
	@echo "Use make buid / make run"

run:
	docker run \
		-it --rm \
		--hostname worker \
		-v $(shell pwd)/ash:/ash/ash \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-e AY_API_KEY=b00b567890123456789012345678iee5 \
		-e AY_SERVER_URL=http://localhost:5000 \
		ynput/ayon-ash:latest

build:
	docker build -t ynput/ayon-ash:latest .

dist: build
	docker push ynput/ayon-ash:latest
