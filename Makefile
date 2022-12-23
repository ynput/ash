default:
	@echo "Use make buid / make run"

build:
	docker build -t openpype/ash:latest .
