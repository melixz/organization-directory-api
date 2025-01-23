# Variables
DOCKER_COMPOSE = docker-compose
PYTHON = poetry run python
DOCKER_EXEC = docker exec
APP_CONTAINER = organization_directory_api

# Default target
.PHONY: all
all: build up migrate seed

# Build and start services
.PHONY: build
build:
	$(DOCKER_COMPOSE) build

.PHONY: up
up:
	$(DOCKER_COMPOSE) up -d

.PHONY: down
down:
	$(DOCKER_COMPOSE) down

.PHONY: restart
restart:
	$(MAKE) down
	$(MAKE) up

# Wait for the database to be ready
.PHONY: wait-for-db
wait-for-db:
	$(DOCKER_EXEC) $(APP_CONTAINER) sh -c "while ! nc -z db 5432; do sleep 1; done"

# Apply Alembic migrations
.PHONY: migrate
migrate: wait-for-db
	$(DOCKER_EXEC) $(APP_CONTAINER) $(PYTHON) -m alembic upgrade head

# Seed mock data into the database
.PHONY: seed
seed:
	$(DOCKER_EXEC) $(APP_CONTAINER) $(PYTHON) src/utils/mock_data.py

# Check logs of the app container
.PHONY: logs
logs:
	$(DOCKER_COMPOSE) logs -f app

# Clean up Docker volumes
.PHONY: clean
clean:
	$(DOCKER_COMPOSE) down -v

# Remove all containers and rebuild
.PHONY: reset
reset: clean build up migrate seed
