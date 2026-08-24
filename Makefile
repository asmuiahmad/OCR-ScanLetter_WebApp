.PHONY: help install run test clean docker-build docker-run docker-stop

help: ## Show this help message
	@echo "OCR Scan Letter WebApp - Development Commands"
	@echo "============================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	@echo "Installing dependencies..."
	pip install -r requirements.txt

run: ## Run the application
	@echo "Starting OCR Scan Letter WebApp..."
	python app.py

test: ## Run tests (placeholder)
	@echo "Running tests..."
	@echo "No tests configured yet"

clean: ## Clean up temporary files
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete

docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t ocr-webapp .

docker-run: ## Run with Docker Compose
	@echo "Starting with Docker Compose..."
	docker-compose up -d

docker-stop: ## Stop Docker containers
	@echo "Stopping Docker containers..."
	docker-compose down

setup: ## Initial setup
	@echo "Setting up OCR Scan Letter WebApp..."
	@echo "1. Creating virtual environment..."
	python -m venv venv
	@echo "2. Installing dependencies..."
	. venv/bin/activate && pip install -r requirements.txt
	@echo "3. Creating directories..."
	mkdir -p instance static/ocr/uploads static/ocr/surat_masuk static/ocr/surat_keluar generated
	@echo "4. Setup complete!"
	@echo "To run: make run"

dev: ## Run in development mode
	@echo "Running in development mode..."
	FLASK_ENV=development FLASK_DEBUG=1 python app.py

prod: ## Run in production mode
	@echo "Running in production mode..."
	FLASK_ENV=production python app.py

format: ## Format code with black
	@echo "Formatting code..."
	black .

lint: ## Lint code with flake8
	@echo "Linting code..."
	flake8 .

check: ## Check code quality
	@echo "Checking code quality..."
	@echo "1. Formatting..."
	@make format
	@echo "2. Linting..."
	@make lint
	@echo "3. Syntax check..."
	python -m py_compile app.py config/*.py

backup: ## Backup database
	@echo "Backing up database..."
	cp instance/app.db instance/app.db.backup.$(shell date +%Y%m%d_%H%M%S)

restore: ## Restore database from backup
	@echo "Available backups:"
	@ls -la instance/app.db.backup.* 2>/dev/null || echo "No backups found"
	@echo "To restore: cp instance/app.db.backup.YYYYMMDD_HHMMSS instance/app.db"

logs: ## Show application logs
	@echo "Application logs:"
	@tail -f *.log 2>/dev/null || echo "No log files found"

status: ## Show application status
	@echo "OCR Scan Letter WebApp Status"
	@echo "============================="
	@echo "Python version: $(shell python --version)"
	@echo "Flask version: $(shell python -c "import flask; print(flask.__version__)" 2>/dev/null || echo "Not installed")"
	@echo "Tesseract: $(shell tesseract --version 2>/dev/null | head -1 || echo "Not installed")"
	@echo "Database: $(shell ls -la instance/app.db 2>/dev/null && echo "Exists" || echo "Not found")"
	@echo "Virtual env: $(shell echo $VIRTUAL_ENV || echo "Not activated")" 