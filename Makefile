.PHONY: help install install-full test lint format clean run-tests run-docker stop-docker check check-simple

help:
	@echo "Available commands:"
	@echo "  install      - Install core dependencies"
	@echo "  install-full - Install all dependencies (dev tools, etc.)"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  clean        - Clean generated files"
	@echo "  run-tests    - Run all tests with coverage"
	@echo "  run-docker   - Start Docker services"
	@echo "  stop-docker  - Stop Docker services"
	@echo "  check        - Run full pre-commit checks (slow)"
	@echo "  check-simple - Run basic syntax checks (fast)"

install:
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
	fi
	.venv/bin/pip install -r requirements-minimal.txt

install-full:
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
	fi
	.venv/bin/pip install -r requirements.txt

test:
	.venv/bin/python -m pytest tests/ -v

run-tests:
	.venv/bin/python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint:
	.venv/bin/pylint src/
	.venv/bin/mypy src/

format:
	.venv/bin/black src/ tests/
	.venv/bin/isort src/ tests/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/

run-docker:
	docker-compose up -d

stop-docker:
	docker-compose down

check:
	@if ! .venv/bin/python -c "import pre_commit" 2>/dev/null; then \
		.venv/bin/pip install pre-commit; \
	fi
	.venv/bin/pre-commit run --all-files

check-simple:
	@echo "=== Running basic checks ==="
	@echo "Checking Python syntax..."
	@find src/ -name "*.py" -exec .venv/bin/python -m py_compile {} \;
	@echo "✓ Python syntax check passed"
	@echo "Checking file structure..."
	@test -f src/data/database.py && echo "✓ Database module exists" || echo "✗ Database module missing"
	@test -f src/config/__init__.py && echo "✓ Config module exists" || echo "✗ Config module missing"
	@test -f src/utils/__init__.py && echo "✓ Utils module exists" || echo "✗ Utils module missing"
	@echo "✓ Basic checks completed"

setup: install run-docker
	@echo "Setup complete!"
