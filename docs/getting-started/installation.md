# Installation

## Install Both Tools

Sketcher consists of two command-line tools:

- **`skewer`** (Python) - Processes YAML and generates documentation
- **`sketcher`** (Go) - Executes steps, provisions clusters, runs tests

### Install skewer (Python)

```bash
pip install sketcher
```

### Install sketcher (Go)

**Option 1: Use pre-built binaries**

```bash
cd /path/to/sketcher
sudo cp sketcher-linux-x64 /usr/local/bin/sketcher     # Linux
# or
sudo cp sketcher-mac-arm64 /usr/local/bin/sketcher     # macOS (Apple Silicon)
```

**Option 2: Build from source**

```bash
go build -o sketcher cmd/sketcher/main.go
sudo mv sketcher /usr/local/bin/
```

### Development Builds

```bash
# Build for current platform
just build-go

# Build for all platforms (Linux x64, macOS ARM64)
just build-go-all
```

## Verify Installation

```bash
skewer --help       # Python tool (resolve, generate, clean)
sketcher --help     # Go tool (run, demo, test, clean)
```

## Create Your Skupper Example

```bash
cd my-skupper-example/
```

Create a `skewer.yaml` file describing your example:

```bash
<editor> skewer.yaml
```

## Generate README and Test

```bash
# Generate README.md from your skewer.yaml (Python tool)
skewer generate skewer.yaml

# Run the example steps in demo mode (pauses before cleanup) (Go tool)
sketcher demo skewer.yaml

# Run full automated test (no pause) (Go tool)
sketcher test skewer.yaml

# Debugging flags (works with demo, run, test commands)
sketcher demo skewer.yaml --verbose  # Show debug output (what's executing)
sketcher demo skewer.yaml --debug    # Show debug output on failure
sketcher demo skewer.yaml --quiet    # Suppress progress messages

# Cluster provider options
sketcher demo skewer.yaml --kind        # Use Kind with NodePort ingress
sketcher demo skewer.yaml --kind-lb     # Use Kind with MetalLB (LoadBalancer ingress)
sketcher test skewer.yaml --kind        # Use Kind for test runs
sketcher test skewer.yaml --kind-lb     # Use Kind with LoadBalancer for tests

# Note: Ingress type comparison
#   - Minikube (default): LoadBalancer ingress
#   - Kind (--kind): NodePort ingress
#   - Kind (--kind-lb): LoadBalancer ingress via MetalLB
# macOS users: Kind requires Docker Desktop or Colima to be running
#   - Docker Desktop: NodePort works out-of-the-box
#   - Colima: Start with `colima start --network-address` for direct NodePort access
```

!!! note
    The `sketcher test` command requires both tools - it calls `skewer generate` to create documentation, then runs the execution steps.

## Next Steps

- Learn how to write your `skewer.yaml` file in the [User Guide](../user-guide/writing-skewer-yaml.md)
- See [Common Patterns](../user-guide/common-patterns.md) for typical configurations
- Explore [Use Cases](../user-guide/use-cases.md) for platform-specific workflows
