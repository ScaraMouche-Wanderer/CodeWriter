.PHONY: run test lint format install clean check-env

# Run the application
run:
	python3 app.py

# Run all tests
test:
	python3 -m pytest tests/ -v

# Lint with ruff
lint:
	python3 -m ruff check .

# Format with ruff
format:
	python3 -m ruff format .

# Install to desktop (GNOME app grid)
install:
	./scripts/install.sh

# Check system dependencies
check-env:
	python3 scripts/check_env.py

# Clean Python caches
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
