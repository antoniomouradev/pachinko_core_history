up: ## up with docker-compose
	@docker-compose up -d
	@echo "🎮 run completed."

clear: ## Clear *.pyc files and __pycache__ directories
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
	@echo "🧹 Cleared .pyc files and __pycache__ directories."

init: ## Install required Python dependencies
	@pip install -r requirements.txt
	@echo "✅ Dependencies installed."

run: ## Run with docker-compose with deamon mode
	@docker-compose up --build -d
	@echo "🎮 run completed."

stop: ## Stop the running containers
	@docker-compose down
	@echo "🛑 Stopped running containers."

restart: ## Stop and start the running containers
	@docker-compose down
	@echo "🛑 Stopped running"
	@docker-compose down up --build -d
	@echo "🎮 Simulation completed."

build: ## build with docker-compose
	docker-compose build

erase: ## Clean up Docker containers and images
	@docker-compose down
	@docker system prune -f
	@echo "🧹 Cleaned up Docker containers and images."

log: ## View the simulation logs
	@docker-compose logs -f	

help: ## Display this help message
	@echo "Usage: make [target]"
	@echo "Targets:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: up clear init run stop restart build erase log help
