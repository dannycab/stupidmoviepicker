# YouTube Movie Picker - Development Commands

.PHONY: help install run test clean docker-build docker-run docker-stop lint format

help: ## Show this help message
	@echo "YouTube Movie Picker - Available Commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make [target]\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-15s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

run: ## Run the application locally
	python app.py

test: ## Run tests
	pytest tests/ -v

test-coverage: ## Run tests with coverage
	pytest tests/ --cov=app --cov-report=html --cov-report=term

lint: ## Run linting
	flake8 app.py tests/
	pylint app.py

format: ## Format code
	black app.py tests/
	isort app.py tests/

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/

# Docker commands
docker-build: ## Build Docker image
	docker build -t ytmoviepicker .

docker-run: ## Run with Docker Compose
	docker-compose up -d

docker-run-prod: ## Run production with Docker Compose
	docker-compose -f docker-compose.prod.yml --profile production up -d

docker-logs: ## View Docker logs
	docker-compose logs -f app

docker-stop: ## Stop Docker containers
	docker-compose down

docker-stop-prod: ## Stop production Docker containers
	docker-compose -f docker-compose.prod.yml down

docker-rebuild: ## Rebuild and restart Docker containers
	docker-compose down
	docker-compose up -d --build

# Database commands
init-db: ## Initialize database
	python init_db.py

backup-db: ## Backup database
	cp movies.db movies.db.backup.$(shell date +%Y%m%d_%H%M%S)

# Development setup
setup: install init-db ## Full development setup
	@echo "✅ Development environment ready!"
	@echo "📝 Don't forget to:"
	@echo "   1. Copy .env.example to .env"
	@echo "   2. Add your OMDb API key to .env"
	@echo "   3. Run 'make run' to start the application"
