# Sketcher Use Cases - Practical Guide

**Purpose**: Step-by-step instructions for common Sketcher scenarios organized by platform, environment, and topology.

---

## Table of Contents

1. [macOS Use Cases](#macos-use-cases)
2. [Linux Use Cases](#linux-use-cases)
3. [Hybrid Scenarios](#hybrid-scenarios)
4. [CI/CD Integration](#cicd-integration)
5. [Development Workflows](#development-workflows)
6. [Production Patterns](#production-patterns)

---

## macOS Use Cases

### Use Case 1: Mac + Docker Desktop + Quick Test

**Scenario**: You have Docker Desktop running and want to quickly test a Skupper example.

**Prerequisites**:
- Docker Desktop installed and running
- `kubectl`, `sketcher`, `skewer` installed

**Commands**:
```bash
# Docker Desktop provides Kind-compatible networking
sketcher demo --kind examples/skupper-example-hello-world.yaml

# What happens:
# 1. Creates two Kind clusters (west, east)
# 2. Uses NodePort ingress (localhost:30xxx)
# 3. Deploys hello-world frontend + backend
# 4. Pauses for inspection
# 5. Type 'yes' to cleanup

# Access frontend at: http://localhost:8080
```

**Why `--kind`?**
- Faster than Minikube (~30s vs ~2min startup)
- Lower resource usage
- Docker Desktop networking works out-of-the-box

---

### Use Case 2: Mac + Colima + NodePort Access

**Scenario**: Using Colima instead of Docker Desktop.

**Prerequisites**:
- Colima installed
- Need direct NodePort access

**Commands**:
```bash
# Start Colima with network address flag (required for NodePort)
colima start --network-address

# Verify Colima is running
colima status

# Run demo with Kind
sketcher demo --kind examples/skupper-example-hello-world.yaml

# NodePort services accessible at localhost:30xxx
curl http://localhost:8080/api/health
```

**Troubleshooting**:
```bash
# If NodePort not accessible, check Colima networking:
colima status
# Should show: network: true

# Restart with network flag if needed:
colima stop
colima start --network-address
```

---

### Use Case 3: Mac + Minikube + LoadBalancer Ingress

**Scenario**: Need LoadBalancer ingress (not NodePort).

**Commands**:
```bash
# Terminal 1: Start minikube tunnel (required for LoadBalancer)
minikube tunnel
# Keep this running, requires sudo password

# Terminal 2: Run demo
sketcher demo examples/skupper-example-hello-world.yaml

# LoadBalancer IPs allocated from Minikube IP pool
# No need for --ingress nodeport in Skupper commands
```

**Why Minikube?**
- LoadBalancer ingress (same as cloud providers)
- Better compatibility with Skupper defaults
- No need to modify skewer.yaml for ingress type

**Downsides**:
- Slower startup (~2min)
- Requires `minikube tunnel` running
- Higher resource usage

---

### Use Case 4: Mac + Kind + MetalLB (Best of Both)

**Scenario**: Want Kind's speed + LoadBalancer ingress.

**Commands**:
```bash
# Use --kind-lb flag (auto-installs MetalLB)
sketcher demo --kind-lb examples/skupper-example-hello-world.yaml

# What happens:
# 1. Creates Kind clusters
# 2. Installs MetalLB in each cluster
# 3. Configures LoadBalancer IP pools (172.18.x.x)
# 4. Uses standard Skupper commands (no --ingress nodeport)
```

**Advantages**:
- Fast startup (Kind speed)
- LoadBalancer ingress (no nodeport hacks)
- No need for minikube tunnel
- Production-like behavior

**When to use**:
- CI/CD pipelines (fast + standard ingress)
- Development with LoadBalancer services
- Testing ingress controllers

---

### Use Case 5: Mac + Remote OpenShift + Local Kind

**Scenario**: One site on remote OpenShift, one local for development.

**Prerequisites**:
- OpenShift kubeconfig at `~/.kube/config-openshift`
- Already logged in: `oc login`

**Commands**:
```bash
# Option 1: Let Sketcher auto-create local cluster
sketcher demo --kind skewer.yaml ~/.kube/config-openshift

# Option 2: Pre-create local cluster
kind create cluster --name local-dev
kind get kubeconfig --name local-dev > ~/.kube/config-local
sketcher demo skewer.yaml ~/.kube/config-openshift ~/.kube/config-local
```

**skewer.yaml site order** (important!):
```yaml
sites:
  production:  # First site → first kubeconfig arg
    platform: kubernetes
    namespace: prod
    env:
      KUBECONFIG: ~/.kube/config-openshift
  
  development: # Second site → auto-provisioned or second arg
    platform: kubernetes
    namespace: dev
    env:
      KUBECONFIG: ~/.kube/config-local
```

---

## Linux Use Cases

### Use Case 6: Linux + Kind + Native Networking

**Scenario**: Linux host, want fastest possible cluster startup.

**Commands**:
```bash
# Kind has native networking on Linux (no VM overhead)
sketcher demo --kind examples/skupper-example-hello-world.yaml

# NodePort directly accessible at localhost:30xxx
# No network-address flag needed (unlike Mac with Colima)
```

**Advantages**:
- Native container networking (no bridge complexity)
- Direct localhost NodePort access
- Lower CPU/memory usage than Minikube

---

### Use Case 7: Linux + Rootless Podman + No Kubernetes

**Scenario**: Edge device, no Kubernetes, rootless containers.

**Prerequisites**:
- Podman installed (rootless mode)
- Skupper CLI installed

**Commands**:
```bash
# Use Podman-only example
sketcher demo examples/podman2podman.yaml

# What happens:
# 1. Creates Podman namespaces: west, east
# 2. Runs Skupper router in each namespace
# 3. Creates static link files
# 4. Deploys frontend/backend containers
# 5. No Kubernetes, no root required

# Skupper namespaces at:
ls ~/.local/share/skupper/namespaces/
# west/
# east/
```

**Accessing containers**:
```bash
# List containers in Podman namespace 'west'
podman --namespace west ps

# Execute command in frontend container
podman --namespace west exec -it frontend bash

# View Skupper router logs
podman --namespace west logs skupper-router
```

---

### Use Case 8: Linux + systemd Services + Skupper

**Scenario**: Legacy systemd services need Skupper networking.

**Prerequisites**:
- systemd on Linux host
- Services running as systemd units

**Example** (custom skewer.yaml):
```yaml
sites:
  cloud:
    platform: kubernetes
    namespace: cloud-backend
    env:
      KUBECONFIG: ~/.kube/config-aws
  
  onprem:
    platform: linux
    namespace: onprem-services
    env:
      SKUPPER_PLATFORM: linux

steps:
  - title: Create cloud site
    commands:
      cloud:
        - run: skupper site create cloud --enable-link-access
  
  - title: Create on-prem site
    commands:
      onprem:
        - run: skupper site create onprem
  
  - title: Expose systemd service
    commands:
      onprem:
        - run: skupper connector create legacy-api 8080 --host localhost
```

**Limitations**:
- Skupper router runs as systemd service
- Services must be accessible at localhost:PORT
- Limited to single host

---

### Use Case 9: Linux + k3s Cluster + External Kubeconfig

**Scenario**: Lightweight k3s cluster for edge deployments.

**Prerequisites**:
- k3s installed: `curl -sfL https://get.k3s.io | sh -`
- Kubeconfig at `/etc/rancher/k3s/k3s.yaml`

**Commands**:
```bash
# Copy k3s kubeconfig
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config-k3s
sudo chown $USER:$USER ~/.kube/config-k3s

# Use k3s for both sites (or mix with cloud provider)
sketcher demo skewer.yaml ~/.kube/config-k3s

# k3s provides built-in LoadBalancer via ServiceLB
# No MetalLB or minikube tunnel needed
```

**Why k3s?**
- Minimal resource footprint (~512MB RAM)
- Built-in LoadBalancer (ServiceLB)
- Perfect for edge/IoT devices
- Single binary, easy install

---

## Hybrid Scenarios

### Use Case 10: Podman Edge + Kubernetes Cloud

**Scenario**: IoT device (Podman) connecting to cloud backend (K8s).

**skewer.yaml**:
```yaml
sites:
  edge:
    platform: podman
    namespace: edge-device
    env:
      SKUPPER_PLATFORM: podman
  
  cloud:
    platform: kubernetes
    namespace: cloud-backend
    env:
      KUBECONFIG: ~/.kube/config-aws

steps:
  - title: Create cloud site
    commands:
      cloud:
        - run: skupper site create cloud --enable-link-access
  
  - title: Create edge site
    commands:
      edge:
        - run: skupper site create edge
  
  - title: Link sites
    commands:
      cloud:
        - run: skupper token issue ~/cloud-link.token
      edge:
        - run: skupper token redeem ~/cloud-link.token
```

**Run**:
```bash
# Provide AWS kubeconfig, Podman runs locally
sketcher demo hybrid-edge-cloud.yaml ~/.kube/config-aws
```

---

### Use Case 11: Three Regions (AWS, Azure, GCP)

**Scenario**: Multi-cloud deployment across all three major providers.

**Prerequisites**:
- Kubeconfigs for each cloud:
  - `~/.kube/config-aws` (EKS)
  - `~/.kube/config-azure` (AKS)
  - `~/.kube/config-gcp` (GKE)

**skewer.yaml**:
```yaml
sites:
  aws:
    platform: kubernetes
    namespace: us-east-1
    env:
      KUBECONFIG: ~/.kube/config-aws
  
  azure:
    platform: kubernetes
    namespace: west-europe
    env:
      KUBECONFIG: ~/.kube/config-azure
  
  gcp:
    platform: kubernetes
    namespace: us-central1
    env:
      KUBECONFIG: ~/.kube/config-gcp
```

**Run**:
```bash
# Provide all three kubeconfigs in site order
sketcher demo multi-cloud.yaml \
  ~/.kube/config-aws \
  ~/.kube/config-azure \
  ~/.kube/config-gcp
```

---

## CI/CD Integration

### Use Case 12: GitHub Actions with Kind+MetalLB

**Scenario**: Automated testing in GitHub Actions.

**.github/workflows/test.yaml**:
```yaml
name: Test Skupper Examples
on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install dependencies
        run: |
          # Install Python tools (skewer)
          pip install pyyaml pytest
          pip install sketcher
          
          # Install Go tools (sketcher binary)
          curl -LO https://github.com/skupperproject/sketcher/releases/latest/download/sketcher-linux-x64
          chmod +x sketcher-linux-x64
          sudo mv sketcher-linux-x64 /usr/local/bin/sketcher
          
          # Verify installations
          skewer --help
          sketcher --help
      
      - name: Run tests with Kind+MetalLB
        run: |
          # Use Kind+MetalLB for fast startup + LoadBalancer ingress
          sketcher test --kind-lb skewer.yaml
        
        timeout-minutes: 15
      
      - name: Upload test artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-logs
          path: /tmp/sketcher-*/
```

**Why `--kind-lb` for CI?**
- Fast cluster startup (saves CI minutes)
- LoadBalancer ingress (no ingress type complications)
- Reliable (MetalLB auto-installs, no manual setup)
- Lower resource usage than Minikube

---

### Use Case 13: GitLab CI with Minikube

**Scenario**: GitLab CI/CD pipeline testing.

**.gitlab-ci.yml**:
```yaml
test-skupper:
  stage: test
  image: ubuntu:latest
  
  before_script:
    - apt-get update
    - apt-get install -y curl python3-pip
    - pip3 install pyyaml sketcher
    - curl -LO https://github.com/skupperproject/sketcher/releases/latest/download/sketcher-linux-x64
    - chmod +x sketcher-linux-x64
    - mv sketcher-linux-x64 /usr/local/bin/sketcher
  
  script:
    # Use default Minikube provider
    - sketcher test skewer.yaml
  
  artifacts:
    when: on_failure
    paths:
      - /tmp/sketcher-*
    expire_in: 1 week
  
  timeout: 20m
```

---

### Use Case 14: Pre-commit Hook Validation

**Scenario**: Validate skewer.yaml changes before committing.

**.git/hooks/pre-commit**:
```bash
#!/bin/bash

# Find modified skewer.yaml files
YAML_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep 'skewer.*\.yaml$')

if [ -n "$YAML_FILES" ]; then
  echo "Validating skewer.yaml files..."
  
  for file in $YAML_FILES; do
    # Validate syntax
    python3 -c "import yaml; yaml.safe_load(open('$file'))" || exit 1
    
    # Generate README (ensures YAML is valid)
    skewer generate "$file" --dry-run || exit 1
    
    echo "✓ $file is valid"
  done
fi

exit 0
```

```bash
# Make executable
chmod +x .git/hooks/pre-commit
```

---

## Development Workflows

### Use Case 15: Interactive Demo + Extensions

**Scenario**: Start base demo, then add observability without restart.

**Terminal 1** (main demo):
```bash
# Start base hello-world demo
sketcher demo examples/skupper-example-hello-world.yaml

# Output shows:
# Demo time!
# Sites:
#   west: export KUBECONFIG=/tmp/sketcher-xyz/.kube/config-west
#   east: export KUBECONFIG=/tmp/sketcher-xyz/.kube/config-east
# Frontend URL: http://localhost:8080/
# Are you done (yes)?

# Don't type 'yes' yet - keep demo running
```

**Terminal 2** (extensions):
```bash
# Add Network Observer to running demo
sketcher demo-extend examples/skewer-extend-observability.yaml

# What happens:
# 1. Attaches to running demo context
# 2. Installs Skupper Network Observer
# 3. Exits, leaving demo running

# Add Prometheus monitoring
sketcher demo-extend examples/skewer-extend-prometheus.yaml

# Add load generator
sketcher demo-extend examples/skewer-extend-loadgen.yaml
```

**Terminal 1** (continue):
```bash
# Now inspect with added tools:
# - Network Observer UI: http://localhost:8010/
# - Prometheus metrics: http://localhost:9090/

# When done, type: yes
# → Cleans up everything
```

---

### Use Case 16: Rapid Iteration with --debug

**Scenario**: Debugging a failing skewer.yaml step.

**Commands**:
```bash
# Run with debug output (shows all commands)
sketcher demo --debug --verbose my-example.yaml

# What you see:
# [DEBUG] Executing in site 'west': kubectl create namespace west
# [DEBUG] Command output: namespace/west created
# [DEBUG] Executing in site 'west': skupper site create west
# [ERROR] Command failed: exit status 1
# [DEBUG] Output:
#   Error: Skupper controller not found. Install with:
#     kubectl apply -f https://skupper.io/v2/install.yaml

# Fix skewer.yaml, retry
sketcher demo --debug my-example.yaml
```

**Debug flags**:
- `--debug` - Show output only on failure
- `--verbose` - Show all output (very noisy)
- `--quiet` - Suppress progress (useful for CI)

---

### Use Case 17: Local Development Against Remote Cluster

**Scenario**: Develop locally, test against staging cluster.

**Setup**:
```bash
# Get staging kubeconfig
kubectl config view --flatten > ~/.kube/config-staging

# Create local Kind cluster
kind create cluster --name dev
kind get kubeconfig --name dev > ~/.kube/config-dev
```

**Run**:
```bash
# staging = first site (production-like)
# dev = second site (local Kind)
sketcher demo my-app.yaml \
  ~/.kube/config-staging \
  ~/.kube/config-dev

# Useful for:
# - Testing against real backend (staging)
# - Fast iteration on frontend (local)
# - No need for full multi-cluster setup
```

---

## Production Patterns

### Use Case 18: GitOps with Custom Resources

**Scenario**: Production deployment using Skupper CRs (no CLI).

**Directory structure**:
```
production/
├── base/
│   ├── kustomization.yaml
│   ├── site.yaml
│   ├── connector.yaml
│   └── listener.yaml
├── overlays/
│   ├── us-east/
│   │   └── kustomization.yaml
│   └── eu-west/
│       └── kustomization.yaml
└── skewer.yaml (for testing only)
```

**skewer.yaml** (testing):
```yaml
sites:
  us-east:
    platform: kubernetes
    namespace: production-us
    env:
      KUBECONFIG: ~/.kube/config-us-east
  
  eu-west:
    platform: kubernetes
    namespace: production-eu
    env:
      KUBECONFIG: ~/.kube/config-eu-west

steps:
  - title: Apply base configuration
    commands:
      us-east:
        - run: kubectl apply -k production/overlays/us-east/
      eu-west:
        - run: kubectl apply -k production/overlays/eu-west/
```

**Test before production**:
```bash
# Dry-run validation
sketcher test --dry-run skewer.yaml

# Real test (auto-cleanup)
sketcher test skewer.yaml

# If tests pass, deploy via GitOps (ArgoCD, Flux, etc.)
```

---

### Use Case 19: Blue/Green Deployment Testing

**Scenario**: Test blue/green deployment with Skupper.

**skewer.yaml**:
```yaml
sites:
  blue:
    platform: kubernetes
    namespace: production-blue
    env:
      KUBECONFIG: ~/.kube/config-prod
  
  green:
    platform: kubernetes
    namespace: production-green
    env:
      KUBECONFIG: ~/.kube/config-prod

steps:
  - title: Deploy green version
    commands:
      green:
        - run: kubectl apply -f app-v2.yaml
  
  - title: Link blue and green
    commands:
      blue:
        - run: skupper token issue ~/blue-token
      green:
        - run: skupper token redeem ~/blue-token
  
  - title: Verify green health
    commands:
      green:
        - await_http_ok: [service/app, "http://{}:8080/health"]
  
  - title: Gradual traffic shift
    commands:
      blue:
        - run: kubectl patch service app -p '{"spec":{"selector":{"version":"green"}}}' --dry-run=client
```

---

### Use Case 20: Disaster Recovery Testing

**Scenario**: Test failover between primary and DR site.

**skewer.yaml**:
```yaml
sites:
  primary:
    platform: kubernetes
    namespace: prod-primary
    env:
      KUBECONFIG: ~/.kube/config-us-east
  
  dr:
    platform: kubernetes
    namespace: prod-dr
    env:
      KUBECONFIG: ~/.kube/config-us-west

steps:
  - title: Deploy to both sites
    commands:
      primary:
        - run: kubectl apply -f app.yaml
      dr:
        - run: kubectl apply -f app.yaml
  
  - title: Create Skupper link
    commands:
      primary:
        - run: skupper site create primary --enable-link-access
        - run: skupper listener create app 8080
      dr:
        - run: skupper site create dr
        - run: skupper connector create app 8080
  
  - title: Simulate primary failure
    commands:
      primary:
        - run: kubectl scale deployment app --replicas=0
        - await_resource: deployment/app
  
  - title: Verify DR takes over
    commands:
      dr:
        - await_http_ok: [service/app, "http://{}:8080/health"]
```

---

## Quick Reference

### Command Cheat Sheet

```bash
# Fast local testing (Mac with Docker Desktop)
sketcher demo --kind skewer.yaml

# Fast local testing (Linux)
sketcher demo --kind skewer.yaml

# LoadBalancer ingress (any platform)
sketcher demo --kind-lb skewer.yaml

# Minikube (traditional)
sketcher demo skewer.yaml

# Remote cluster + local auto-provision
sketcher demo skewer.yaml ~/.kube/config-remote

# Two remote clusters
sketcher demo skewer.yaml ~/.kube/config-1 ~/.kube/config-2

# CI/CD automated testing
sketcher test --kind-lb skewer.yaml

# Debug mode
sketcher demo --debug --verbose skewer.yaml

# Interactive extensions
sketcher demo skewer.yaml           # Terminal 1
sketcher demo-extend ext.yaml       # Terminal 2
```

### Platform Decision Tree

```
What platform do I have?

macOS:
  ├─ Docker Desktop running?
  │   ├─ Yes → sketcher demo --kind
  │   └─ No → Install Docker Desktop or Colima
  ├─ Colima running?
  │   ├─ Yes → colima start --network-address && sketcher demo --kind
  │   └─ No → Install Colima
  └─ Want LoadBalancer?
      └─ Yes → sketcher demo --kind-lb (auto-installs MetalLB)

Linux:
  ├─ Have K8s cluster?
  │   ├─ Yes → sketcher demo skewer.yaml ~/.kube/config
  │   └─ No → sketcher demo --kind (fastest)
  ├─ Want rootless containers?
  │   └─ Yes → Use podman2podman.yaml example
  └─ CI/CD pipeline?
      └─ Yes → sketcher test --kind-lb (fast + standard)

Windows:
  └─ Use WSL2 → Follow Linux instructions
```

---

**Last Updated**: 2026-08-07  
**See Also**: `PLAN.md`, `examples-guide.md`, `README.md`
