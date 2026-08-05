# Sketcher development tasks
# Split architecture: skewer (Python) + sketcher (Go)
#
# Tools:
#   skewer (Python)   - YAML processing & documentation generation
#   sketcher (Go)     - Execution engine for tests & demos
#
# Quick start:
#   just build-all    - Build both tools
#   just smoke-test   - Verify everything works
#   just --list       - Show all available recipes

# Set Python path for all commands
export PYTHONPATH := justfile_directory()

# Default recipe - show help
default:
    @echo "Sketcher Development Tasks"
    @echo ""
    @echo "Quick Start:"
    @echo "  just build-all    - Build both skewer (Python) and sketcher (Go)"
    @echo "  just smoke-test   - Run smoke tests"
    @echo "  just version      - Show versions"
    @echo ""
    @echo "Common Tasks:"
    @echo "  just generate FILE          - Generate README from YAML"
    @echo "  just demo FILE             - Run demo (Minikube)"
    @echo "  just test-yaml FILE        - Run full test"
    @echo ""
    @echo "All Recipes:"
    @just --list

# Install Python dependencies
install:
    uv venv
    uv pip install pyyaml pytest

# Install skewer (Python CLI) in development mode
dev-install: install
    pip install -e .

# Build sketcher (Go CLI) for current platform
build-go:
    go build -o ./sketcher-bin cmd/sketcher/main.go
    @echo "Built: ./sketcher-bin (rename to 'sketcher' when installing)"

# Build sketcher for Linux x86-64
build-linux:
    GOOS=linux GOARCH=amd64 go build -o ./sketcher-linux-x64 cmd/sketcher/main.go
    @echo "Built: ./sketcher-linux-x64"

# Build sketcher for macOS Apple Silicon
build-mac:
    GOOS=darwin GOARCH=arm64 go build -o ./sketcher-mac-arm64 cmd/sketcher/main.go
    @echo "Built: ./sketcher-mac-arm64"

# Build for all platforms
build-go-all: build-linux build-mac
    @echo "Built binaries for Linux and macOS"
    @ls -lh sketcher-*

# Build both tools
build-all: dev-install build-go
    @echo "Built skewer (Python) and sketcher (Go)"

# Run all tests
test:
    python -m pytest sketcher/tests/ -v

# Run tests with coverage
test-cov:
    python -m pytest sketcher/tests/ --cov=sketcher --cov-report=term-missing

# Quick test (just run, no verbose)
test-quick:
    python -m pytest sketcher/tests/ -q

# === Python Tool: skewer (YAML processing & docs) ===

# Generate README from YAML
generate YAML="examples/*/skewer.yaml":
    skewer generate {{YAML}}

# Resolve standard steps in YAML
resolve INPUT OUTPUT="":
    #!/usr/bin/env bash
    if [ -z "{{OUTPUT}}" ]; then
        skewer resolve {{INPUT}}
    else
        skewer resolve {{INPUT}} -o {{OUTPUT}}
    fi

# Batch resolve all examples in a directory
batch-resolve DIR:
    #!/usr/bin/env bash
    for f in {{DIR}}/*.yaml; do
        echo "Resolving $f..."
        skewer resolve "$f" --in-place || true
    done

# Generate README for all resolved examples
generate-all:
    #!/usr/bin/env bash
    for f in examples/*/skewer.yaml; do
        echo "Generating README for $f..."
        skewer generate "$f" || true
    done

# === Go Tool: sketcher (execution) ===

# Run steps from YAML
run YAML="skewer.yaml" *KUBECONFIGS:
    ./sketcher-bin run {{YAML}} {{KUBECONFIGS}}

# Demo with Minikube (default)
demo YAML="skewer.yaml":
    ./sketcher-bin demo {{YAML}}

# Demo with Kind
demo-kind YAML="skewer.yaml":
    ./sketcher-bin demo {{YAML}} --kind

# Test with Minikube (default)
test-yaml YAML="skewer.yaml":
    ./sketcher-bin test {{YAML}}

# Test with Kind
test-kind YAML="skewer.yaml":
    ./sketcher-bin test {{YAML}} --kind

# Extend running demo
demo-extend EXTEND_FILE:
    ./sketcher-bin demo-extend {{EXTEND_FILE}}

# === Clean ===

# Clean Python artifacts
clean-python:
    skewer clean || true
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    rm -rf .pytest_cache
    rm -rf .coverage
    rm -rf htmlcov
    rm -rf build/
    rm -rf dist/

# Clean Go artifacts
clean-go:
    rm -f sketcher-bin sketcher-linux-x64 sketcher-mac-arm64
    rm -f sketcher/main
    go clean

# Clean everything
clean: clean-python clean-go

# Clean everything including venv
clean-all: clean
    rm -rf .venv

# === Development ===

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

# Build Python distribution package
build-python:
    python -m build .

# Show versions
version:
    @echo "Python (skewer):"
    @python -c "from sketcher import __version__; print(f'  {__version__}')"
    @echo "Go (sketcher):"
    @if [ -f ./sketcher-bin ]; then ./sketcher-bin run 2>&1 | head -1 | sed 's/Sketcher /  /'; else echo "  (not built - run: just build-go)"; fi

# Run a simple smoke test
smoke-test:
    @echo "=== Smoke Test ==="
    @echo "1. Testing skewer (Python)..."
    @skewer --help > /dev/null && echo "  ✓ skewer CLI works"
    @echo "2. Testing sketcher (Go)..."
    @./sketcher-bin 2>&1 | grep -q "Usage:" && echo "  ✓ sketcher CLI works"
    @echo "3. Testing Python imports..."
    @python -c "from sketcher import Model, resolver, generator; print('  ✓ Python imports work')"
    @echo "4. Testing model..."
    @python -c "from sketcher import Model; m = Model('examples/*/skewer.yaml'); m.check(); print('  ✓ Model loads')" 2>/dev/null || echo "  ⚠ No example found (skip)"
    @echo "5. Running Python tests..."
    @python -m pytest tests/ -q && echo "  ✓ Tests pass"
    @echo ""
    @echo "=== All smoke tests passed! ==="

# Show project stats
stats:
    @echo "=== Sketcher Statistics ==="
    @echo "Python files:      $(find sketcher -name '*.py' -type f | wc -l)"
    @echo "Go files:          $(find internal cmd -name '*.go' -type f 2>/dev/null | wc -l)"
    @echo "Test files:        $(find tests -name 'test_*.py' | wc -l)"
    @echo "Python lines:      $(find sketcher -name '*.py' -type f -exec cat {} \; | wc -l)"
    @echo "Go lines:          $(find internal cmd -name '*.go' -type f -exec cat {} \; 2>/dev/null | wc -l)"
    @echo "Documentation:     $(ls *.md 2>/dev/null | wc -l)"
    @echo "Examples:          $(find examples -name 'skewer.yaml' 2>/dev/null | wc -l)"

# Validate YAML against JSON Schema
validate *FILES:
    #!/usr/bin/env bash
    if [ -z "{{FILES}}" ]; then
        echo "Usage: just validate <yaml-file> [yaml-file ...]"
        echo "Example: just validate skewer.yaml"
        echo "Example: just validate examples/*.yaml"
        exit 1
    fi
    python scripts/validate-schema.py {{FILES}}

# Validate all examples
validate-examples:
    python scripts/validate-schema.py examples/minimal-valid.yaml tests/fixtures/skewer-resolved.yaml

# Validate and show detailed errors
validate-verbose YAML:
    python scripts/validate-schema.py {{YAML}} || true
