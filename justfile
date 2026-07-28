# Sketcher development tasks

# Set Python path for all commands
export PYTHONPATH := justfile_directory()

# Default recipe - show help
default:
    @just --list

# Install dependencies
install:
    uv venv
    uv pip install pyyaml pytest

# Install sketcher in development mode
dev-install: install
    pip install -e sketcher/

# Run all tests
test:
    python -m pytest sketcher/tests/ -v

# Run tests with coverage
test-cov:
    python -m pytest sketcher/tests/ --cov=sketcher --cov-report=term-missing

# Quick test (just run, no verbose)
test-quick:
    python -m pytest sketcher/tests/ -q

# Run sketcher CLI (with proper PYTHONPATH)
sketcher *ARGS:
    python -m sketcher {{ARGS}}

# Demo with Minikube (default)
demo YAML="skewer.yaml":
    python -m sketcher demo {{YAML}}

# Demo with Kind
demo-kind YAML="skewer.yaml":
    python -m sketcher demo {{YAML}} --kind

# Test with Minikube (default)
test-yaml YAML="skewer.yaml":
    python -m sketcher test {{YAML}}

# Test with Kind
test-kind YAML="skewer.yaml":
    python -m sketcher test {{YAML}} --kind

# Generate README for an example
generate YAML="sketcher_yamls/skupper-example-hello-world.yaml":
    python -m sketcher generate {{YAML}}

# Resolve a yaml file
resolve INPUT OUTPUT="":
    #!/usr/bin/env bash
    if [ -z "{{OUTPUT}}" ]; then
        python -m sketcher resolve {{INPUT}}
    else
        python -m sketcher resolve {{INPUT}} -o {{OUTPUT}}
    fi

# Batch resolve all examples in a directory
batch-resolve DIR:
    #!/usr/bin/env bash
    for f in {{DIR}}/*.yaml; do
        echo "Resolving $f..."
        python -m sketcher resolve "$f" --in-place || true
    done

# Clean generated files
clean:
    python -m sketcher clean
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
    @command -v black >/dev/null 2>&1 && black sketcher/ || echo "black not installed"

# Lint code (if ruff is installed)
lint:
    @command -v ruff >/dev/null 2>&1 && ruff check sketcher/ || echo "ruff not installed"

# Type check (if mypy is installed)
typecheck:
    @command -v mypy >/dev/null 2>&1 && mypy sketcher/ || echo "mypy not installed"

# Run all quality checks
check: test lint typecheck

# Build distribution package
build:
    python -m build sketcher/

# Show sketcher version
version:
    python -c "import sys; sys.path.insert(0, 'sketcher'); import sketcher; print(sketcher.__version__)"

# Generate README for all resolved examples
generate-all:
    #!/usr/bin/env bash
    for f in sketcher_yamls/*.yaml; do
        echo "Generating README for $f..."
        python -m sketcher generate "$f" || true
    done

# Run a simple smoke test
smoke-test:
    @echo "=== Smoke Test ==="
    @echo "1. Testing CLI..."
    @python -m sketcher --help > /dev/null && echo "  ✓ CLI works"
    @echo "2. Testing imports..."
    @python -c "from sketcher import Model; print('  ✓ Model imports')"
    @echo "3. Testing model..."
    @python -c "from sketcher import Model; m = Model('sketcher_yamls/skupper-example-hello-world.yaml'); m.check(); print('  ✓ Model loads')"
    @echo "4. Running tests..."
    @python -m pytest sketcher/tests/ -q && echo "  ✓ Tests pass"
    @echo ""
    @echo "=== All smoke tests passed! ==="

# Show project stats
stats:
    @echo "=== Sketcher Statistics ==="
    @echo "Python files:     $(find sketcher -name '*.py' -type f | wc -l)"
    @echo "Test files:       $(find sketcher/tests -name 'test_*.py' | wc -l)"
    @echo "Total lines:      $(find sketcher -name '*.py' -type f -exec cat {} \; | wc -l)"
    @echo "Documentation:    $(find sketcher -name '*.md' | wc -l)"
    @echo "Resolved examples: $(ls sketcher_yamls/*.yaml 2>/dev/null | wc -l)"
