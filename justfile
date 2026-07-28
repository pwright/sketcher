# Phoenix development tasks

# Set Python path for all commands
export PYTHONPATH := justfile_directory()

# Default recipe - show help
default:
    @just --list

# Install dependencies
install:
    uv venv
    uv pip install pyyaml pytest

# Install phoenix in development mode
dev-install: install
    pip install -e phoenix/

# Run all tests
test:
    python -m pytest phoenix/tests/ -v

# Run tests with coverage
test-cov:
    python -m pytest phoenix/tests/ --cov=phoenix --cov-report=term-missing

# Quick test (just run, no verbose)
test-quick:
    python -m pytest phoenix/tests/ -q

# Run phoenix CLI (with proper PYTHONPATH)
phoenix *ARGS:
    python -m phoenix {{ARGS}}

# Demo with Minikube (default)
demo YAML="skewer.yaml":
    python -m phoenix demo {{YAML}}

# Demo with Kind
demo-kind YAML="skewer.yaml":
    python -m phoenix demo {{YAML}} --kind

# Test with Minikube (default)
test-yaml YAML="skewer.yaml":
    python -m phoenix test {{YAML}}

# Test with Kind
test-kind YAML="skewer.yaml":
    python -m phoenix test {{YAML}} --kind

# Generate README for an example
generate YAML="phoenix_yamls/skupper-example-hello-world.yaml":
    python -m phoenix generate {{YAML}}

# Resolve a yaml file
resolve INPUT OUTPUT="":
    #!/usr/bin/env bash
    if [ -z "{{OUTPUT}}" ]; then
        python -m phoenix resolve {{INPUT}}
    else
        python -m phoenix resolve {{INPUT}} -o {{OUTPUT}}
    fi

# Batch resolve all examples in a directory
batch-resolve DIR:
    #!/usr/bin/env bash
    for f in {{DIR}}/*.yaml; do
        echo "Resolving $f..."
        python -m phoenix resolve "$f" --in-place || true
    done

# Clean generated files
clean:
    python -m phoenix clean
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    rm -rf .pytest_cache
    rm -rf .coverage
    rm -rf htmlcov

# Clean everything including venv
clean-all: clean
    rm -rf .venv

# Format code (if black is installed)
format:
    @command -v black >/dev/null 2>&1 && black phoenix/ || echo "black not installed"

# Lint code (if ruff is installed)
lint:
    @command -v ruff >/dev/null 2>&1 && ruff check phoenix/ || echo "ruff not installed"

# Type check (if mypy is installed)
typecheck:
    @command -v mypy >/dev/null 2>&1 && mypy phoenix/ || echo "mypy not installed"

# Run all quality checks
check: test lint typecheck

# Build distribution package
build:
    python -m build phoenix/

# Show phoenix version
version:
    python -c "import sys; sys.path.insert(0, 'phoenix'); import phoenix; print(phoenix.__version__)"

# Generate README for all resolved examples
generate-all:
    #!/usr/bin/env bash
    for f in phoenix_yamls/*.yaml; do
        echo "Generating README for $f..."
        python -m phoenix generate "$f" || true
    done

# Run a simple smoke test
smoke-test:
    @echo "=== Smoke Test ==="
    @echo "1. Testing CLI..."
    @python -m phoenix --help > /dev/null && echo "  ✓ CLI works"
    @echo "2. Testing imports..."
    @python -c "from phoenix import Model; print('  ✓ Model imports')"
    @echo "3. Testing model..."
    @python -c "from phoenix import Model; m = Model('phoenix_yamls/skupper-example-hello-world.yaml'); m.check(); print('  ✓ Model loads')"
    @echo "4. Running tests..."
    @python -m pytest phoenix/tests/ -q && echo "  ✓ Tests pass"
    @echo ""
    @echo "=== All smoke tests passed! ==="

# Show project stats
stats:
    @echo "=== Phoenix Statistics ==="
    @echo "Python files:     $(find phoenix -name '*.py' -type f | wc -l)"
    @echo "Test files:       $(find phoenix/tests -name 'test_*.py' | wc -l)"
    @echo "Total lines:      $(find phoenix -name '*.py' -type f -exec cat {} \; | wc -l)"
    @echo "Documentation:    $(find phoenix -name '*.md' | wc -l)"
    @echo "Resolved examples: $(ls phoenix_yamls/*.yaml 2>/dev/null | wc -l)"
