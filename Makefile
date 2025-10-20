.PHONY: help build up down logs shell test clean

# Variables
DOCKER_COMPOSE = docker-compose
DOCKER = docker
IMAGE_NAME = raganything-api
CONTAINER_NAME = raganything-api

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker image
	$(DOCKER_COMPOSE) build

up: ## Start services
	$(DOCKER_COMPOSE) up -d
	@echo "✓ Services started"
	@echo "API running at: http://localhost:8000"
	@echo "Health check: http://localhost:8000/health"

down: ## Stop services
	$(DOCKER_COMPOSE) down

restart: down up ## Restart services

logs: ## Show logs
	$(DOCKER_COMPOSE) logs -f

logs-api: ## Show API logs only
	$(DOCKER_COMPOSE) logs -f raganything-api

shell: ## Open shell in container
	$(DOCKER) exec -it $(CONTAINER_NAME) /bin/bash

test: ## Run API tests
	python test_api.py --url http://localhost:8000

test-remote: ## Run API tests against remote server
	@read -p "Enter API URL: " url; \
	read -p "Enter API Key: " key; \
	python test_api.py --url $$url --api-key $$key

health: ## Check API health
	@curl -s http://localhost:8000/health | python -m json.tool

clean: ## Clean up containers and volumes
	$(DOCKER_COMPOSE) down -v
	@echo "✓ Cleaned up containers and volumes"

clean-all: clean ## Clean up everything including images
	$(DOCKER) rmi $(IMAGE_NAME) || true
	@echo "✓ Cleaned up images"

env: ## Create .env file from template
	@if [ ! -f .env ]; then \
		cp .env.docker .env; \
		echo "✓ Created .env file from template"; \
		echo "⚠️  Please edit .env and add your API keys"; \
	else \
		echo "⚠️  .env file already exists"; \
	fi

dev: ## Start in development mode (with logs)
	$(DOCKER_COMPOSE) up

status: ## Show container status
	$(DOCKER_COMPOSE) ps

stats: ## Show container resource usage
	$(DOCKER) stats $(CONTAINER_NAME)

pull: ## Pull latest changes and rebuild
	git pull
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) up -d
	@echo "✓ Updated and restarted"
