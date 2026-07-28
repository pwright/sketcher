# Kind Support in Sketcher ✅

## Summary

Sketcher now supports **Kind** as an alternative to Minikube for local Kubernetes testing!

## What's New

### 1. Kind Module (`kind.py`)
- 120 lines of clean Python 3
- Context manager like Minikube
- NodePort ingress support (ports 8080, 8443, 8010)
- Auto-cleanup on exit

### 2. CLI Flags
Added `--kind` flag to:
- `sketcher demo --kind` - Run demo with Kind instead of Minikube
- `sketcher test --kind` - Run full test suite with Kind

### 3. Just Recipes
```bash
just demo-kind YAML      # Demo with Kind
just test-kind YAML      # Test with Kind
```

## Usage

### Basic Demo
```bash
# Minikube (default)
sketcher demo skewer.yaml

# Kind
sketcher demo skewer.yaml --kind
```

### Full Test Suite
```bash
# Minikube (default)
sketcher test skewer.yaml

# Kind
sketcher test skewer.yaml --kind
```

### Python API
```python
from sketcher import kind, executor

# Use Kind instead of Minikube
with kind.Kind("skewer.yaml") as k:
    executor.run_steps("skewer.yaml", kubeconfigs=k.kubeconfigs)
```

## How It Works

### Kind Cluster Creation
```yaml
# Auto-generated Kind config
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 8080
    protocol: TCP
  - containerPort: 30443
    hostPort: 8443
    protocol: TCP
  - containerPort: 30010
    hostPort: 8010
    protocol: TCP
```

### Port Mappings
- **30080 → 8080** - HTTP frontend (NodePort)
- **30443 → 8443** - HTTPS services (NodePort)
- **30010 → 8010** - Skupper console (NodePort)

### Cluster Lifecycle
1. **Create:** `kind create cluster --name skewer --config kind-config.yaml`
2. **Use:** Generate kubeconfigs for each site
3. **Cleanup:** `kind delete cluster --name skewer`

## Comparison: Kind vs Minikube

| Feature | Minikube | Kind |
|---------|----------|------|
| Speed | Slower startup | Faster startup |
| Ingress | LoadBalancer (tunnel) | NodePort |
| Resource usage | Higher | Lower |
| Docker-in-Docker | No | Yes |
| CI/CD friendly | Moderate | Excellent |
| Default | ✅ Yes | No (use --kind) |

## When to Use Kind

✅ **Use Kind when:**
- Running in CI/CD (GitHub Actions, etc.)
- Need faster startup times
- Working in Docker-based environments
- Want lighter resource usage
- NodePort ingress is acceptable

✅ **Use Minikube when:**
- Need LoadBalancer ingress (default behavior)
- Testing production-like scenarios
- Don't mind slower startup
- Minikube is already installed

## Requirements

### Install Kind
```bash
# On Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# On macOS
brew install kind

# Verify
kind version
```

### Install kubectl
```bash
# Kind requires kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/kubectl
```

## Examples

### Demo Mode
```bash
# Start demo with Kind
sketcher demo sketcher_yamls/skupper-example-hello-world.yaml --kind

# Kind cluster created: skewer
# Services accessible via NodePort
# Console: http://localhost:8010/
# Frontend: http://localhost:8080/
```

### Test Suite
```bash
# Run full test suite with Kind
sketcher test sketcher_yamls/skupper-example-hello-world.yaml --kind

# 1. Generates README
# 2. Creates Kind cluster
# 3. Runs main steps
# 4. Runs extension files
# 5. Cleans up Kind cluster
```

### CI/CD Integration
```yaml
# GitHub Actions example
name: Test Skupper Example
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Kind
        run: |
          curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
          chmod +x ./kind
          sudo mv ./kind /usr/local/bin/kind
      
      - name: Install Sketcher
        run: pip install -e sketcher/
      
      - name: Run Tests with Kind
        run: |
          export PYTHONPATH=$PWD:$PYTHONPATH
          python -m sketcher test skewer.yaml --kind
```

## Implementation Details

### Kind Class Structure
```python
class Kind:
    """Context manager for Kind-based testing."""
    
    def __init__(self, yaml_file: str):
        self.yaml_file = yaml_file
        self.kubeconfigs: List[str] = []
        self.work_dir = Path(tempfile.gettempdir()) / "sketcher"
        self.cluster_name = "skewer"
    
    def __enter__(self):
        # Create Kind cluster with NodePort config
        # Generate kubeconfigs for each site
        # Return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        # Delete Kind cluster
        # Cleanup work directory
```

### Error Handling
```python
# Prevents conflicts
if self.cluster_name in existing_clusters:
    raise SketcherError(
        f"A Kind cluster '{self.cluster_name}' already exists. "
        f"Delete it using 'kind delete cluster --name {self.cluster_name}'."
    )

# Cleanup on failure
try:
    # Create and configure cluster
except Exception:
    utils.run(f"kind delete cluster --name {self.cluster_name}", check=False)
    raise
```

## Troubleshooting

### "cluster 'skewer' already exists"
```bash
# Delete existing cluster
kind delete cluster --name skewer

# Then retry
sketcher demo skewer.yaml --kind
```

### "kind: command not found"
```bash
# Install Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### NodePort services not accessible
```bash
# Check port mappings
docker ps | grep skewer

# Should show ports 8080, 8443, 8010 mapped
```

## Benefits

✨ **Faster CI/CD** - Kind starts in seconds vs minutes for Minikube
✨ **Lower resources** - Runs in Docker, no VM overhead
✨ **Better isolation** - Each cluster in its own container
✨ **Easy cleanup** - Just delete cluster, no VM artifacts
✨ **Standard tooling** - Uses standard kubectl and kind CLI

## Files Added

- `sketcher/kind.py` (120 lines) - Kind integration
- `sketcher/KIND-SUPPORT.md` (this file) - Documentation

## Files Modified

- `sketcher/cli.py` - Added --kind flag to demo/test commands
- `sketcher/__init__.py` - Export kind module
- `justfile` - Added demo-kind and test-kind recipes
- `AGENTS.md` - Updated to show Kind support implemented

## Status

✅ **Fully Implemented**
✅ **CLI flags working** (--kind on demo/test)
✅ **Just recipes added** (demo-kind, test-kind)
✅ **Documentation complete**
✅ **AGENTS.md requirement satisfied**

**Sketcher now supports both Minikube (default) and Kind (--kind flag)!** 🚀
