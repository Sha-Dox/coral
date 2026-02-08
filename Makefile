.PHONY: help install start stop restart clean docker-build docker-up docker-down lint format

help:
	@echo "CORAL - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install       - Install dependencies"
	@echo "  make start         - Start all services"
	@echo "  make stop          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make docker-logs   - View Docker logs"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make security      - Run security checks"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         - Clean temporary files"
	@echo "  make backup        - Backup database"
	@echo "  make logs          - View logs"

install:
	@echo "Installing dependencies..."
	cd coral && pip3 install -r requirements.txt
	@echo "✓ Dependencies installed"

start:
	@echo "Starting CORAL services..."
	./start_all.sh

stop:
	@echo "Stopping CORAL services..."
	@pkill -f "python.*app.py" || true
	@pkill -f "python.*monitor.py" || true
	@echo "✓ Services stopped"

restart: stop start

docker-build:
	@echo "Building Docker images..."
	docker-compose build
	@echo "✓ Docker images built"

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d
	@echo "✓ Docker containers started"
	@echo "CORAL Hub: http://localhost:5002"

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down
	@echo "✓ Docker containers stopped"

docker-logs:
	docker-compose logs -f

lint:
	@echo "Running linters..."
	flake8 . --exclude=venv,env,.git,__pycache__,instagram_monitor,pinterest_monitor,spotify_monitor,maigret,snapchat_monitor --max-line-length=127
	@echo "✓ Linting complete"

format:
	@echo "Formatting code..."
	black --exclude='venv|env|\.git|instagram_monitor|pinterest_monitor|spotify_monitor|maigret|snapchat_monitor' .
	@echo "✓ Formatting complete"

security:
	@echo "Running security checks..."
	bandit -r . --exclude './venv,./env,./instagram_monitor,./pinterest_monitor,./spotify_monitor,./maigret,./snapchat_monitor' || true
	@echo "✓ Security check complete"

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✓ Cleanup complete"

backup:
	@echo "Backing up database..."
	@mkdir -p backups
	@cp coral/coral.db backups/coral_$(shell date +%Y%m%d_%H%M%S).db 2>/dev/null || echo "No database to backup"
	@echo "✓ Backup complete"

logs:
	@echo "Recent logs:"
	@tail -n 50 /tmp/coral.log 2>/dev/null || echo "No logs found"
