# Installation

## Quick Install (Recommended)

**For most users**: Install the `sketcher` command-line tool to run and test Skupper examples.

=== "Linux / macOS"
    ```bash
    curl https://pwright.github.io/sketcher/install.sh | sh
    ```

=== "Manual Download"
    ```bash
    # Linux
    curl -LO https://github.com/pwright/sketcher/releases/latest/download/sketcher-linux
    chmod +x sketcher-linux
    sudo mv sketcher-linux /usr/local/bin/sketcher

    # macOS (Apple Silicon)
    curl -LO https://github.com/pwright/sketcher/releases/latest/download/sketcher-mac-arm64
    chmod +x sketcher-mac-arm64
    sudo mv sketcher-mac-arm64 /usr/local/bin/sketcher

    # macOS (Intel)
    curl -LO https://github.com/pwright/sketcher/releases/latest/download/sketcher-mac-amd64
    chmod +x sketcher-mac-amd64
    sudo mv sketcher-mac-amd64 /usr/local/bin/sketcher
    ```

**Installation options:**

```bash
# Interactive mode (asks before installing)
curl https://pwright.github.io/sketcher/install.sh | sh -s -- --interactive

# Install to /opt/sketcher/bin instead of ~/.local/bin
curl https://pwright.github.io/sketcher/install.sh | sh -s -- --scheme opt

# Install specific version
curl https://pwright.github.io/sketcher/install.sh | sh -s -- --version v1.0.0
```

## Verify Installation

```bash
sketcher --help     # Should show sketcher commands
sketcher --version  # Should show version number
```

## For Example Authors

**Only needed if you're creating Skupper examples and need to generate README documentation.**

Sketcher uses two tools:

- **`sketcher`** (Go) - Executes steps, provisions clusters, runs tests *(installed above)*
- **`skewer`** (Python) - Generates documentation from YAML

Most users only need `sketcher`. Install `skewer` if you need to:

- Generate or update README.md files from `skewer.yaml`
- Create new Skupper examples
- Use `skewer resolve` to migrate old YAML files

**Install skewer (Python):**

```bash
pip install sketcher
```

**Verify both tools:**

```bash
skewer --help       # Python tool (resolve, generate, clean)
sketcher --help     # Go tool (run, demo, test, clean)
```

## Advanced: Build from Source

**Building the Go binary:**

```bash
# Clone the repository
git clone https://github.com/pwright/sketcher
cd sketcher

# Build for current platform
just build-go

# Build for all platforms (Linux x64, macOS ARM64, macOS Intel)
just build-go-all

# Install locally
sudo cp build/sketcher-* /usr/local/bin/sketcher
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
