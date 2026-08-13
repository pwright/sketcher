# Sketcher Use Cases - Practical Guide

**Purpose**: Choose the right Sketcher approach for your environment and test goals.

This guide helps you select platform options, cluster providers, and workflows based on what you need to accomplish. Each use case includes the exact commands and configuration needed.

---

## How to Use This Guide

Find the section matching what you need to do:

- **[Quick Start Testing](#quick-start-testing)** - Try Sketcher with minimal setup
- **[Choose Your Platform](#choose-your-platform)** - Pick the right cluster provider for macOS, Linux, or hybrid setups
- **[Automate Testing](#automate-testing)** - Set up CI/CD pipelines and pre-commit validation
- **[Develop Iteratively](#develop-iteratively)** - Debug, extend demos, and test against remote clusters
- **[Production Validation](#production-validation)** - GitOps, blue/green, and disaster recovery testing
- **[Troubleshoot Problems](#troubleshoot-problems)** - Resolve networking, ingress, and configuration issues

---

## Quick Start Testing

### Test a Skupper example in under 60 seconds

**What you need**: Docker Desktop (macOS) or Docker (Linux) running.

**Run this**:
```bash
cd your-example-directory/
sketcher demo --kind skewer.yaml
```

**What happens**:
1. Creates two Kind clusters (west, east) in ~30 seconds
2. Runs your example steps
3. Displays connection info and pauses for inspection
4. Type `yes` to clean up

**Access the application**: Open `http://localhost:8080` (exact port shown in demo output).

**Why this works**: Kind with NodePort ingress requires no tunnel, no MetalLB installation, just Docker.

**Next steps**: 
- See [Choose Your Platform](#choose-your-platform) if you need LoadBalancer ingress
- See [Develop Iteratively](#develop-iteratively) to add observability to a running demo

---

## Choose Your Platform

Select the cluster provider that fits your environment and performance needs.

### macOS: Docker Desktop (Fastest)

**When to use**: You have Docker Desktop installed and want the fastest local testing.

**Command**:
```bash
sketcher demo --kind examples/skupper-example-hello-world.yaml
```

**Characteristics**:
- Startup time: ~30 seconds
- Ingress type: NodePort (localhost:30xxx)
- Resource usage: Low
- LoadBalancer support: No (use `--kind-lb` instead)

**Limitations**: Skupper commands must include `--ingress nodeport --ingress-host localhost` flags.

---

### macOS: Colima (Docker Alternative)

**When to use**: You prefer Colima over Docker Desktop.

**Setup**:
```bash
# Required for NodePort access
colima start --network-address

# Verify
colima status  # Should show: network: true
```

**Command**:
```bash
sketcher demo --kind examples/skupper-example-hello-world.yaml
```

**Troubleshooting**: If `localhost:30xxx` not accessible, restart Colima with `--network-address` flag.

---

### macOS/Linux: Kind + MetalLB (Best Balance)

**When to use**: You want Kind's speed + standard LoadBalancer ingress (no nodeport configuration).

**Command**:
```bash
sketcher demo --kind-lb examples/skupper-example-hello-world.yaml
```

**What this does**:
1. Creates Kind clusters (fast startup)
2. Auto-installs MetalLB in each cluster
3. Allocates LoadBalancer IPs (172.18.x.x range)
4. Uses standard Skupper commands (no `--ingress nodeport` needed)

**Advantages over plain `--kind`**:
- No ingress type configuration in skewer.yaml
- Production-like LoadBalancer behavior
- Faster than Minikube (~30s vs ~2min startup)

**Recommended for**: CI/CD pipelines, development with LoadBalancer services.

---

### macOS: Minikube (Full Compatibility)

**When to use**: You need complete Skupper CLI compatibility with no configuration changes.

**Setup** (requires running tunnel):
```bash
# Terminal 1 - Keep this running
minikube tunnel

# Terminal 2 - Run demo
sketcher demo examples/skupper-example-hello-world.yaml
```

**Characteristics**:
- Startup time: ~2 minutes
- Ingress type: LoadBalancer (requires tunnel)
- Resource usage: Higher than Kind
- Compatibility: Best (matches cloud providers)

**Downsides**: Slower startup, requires persistent `minikube tunnel`, higher CPU/memory.

---

### Linux: Kind (Native Performance)

**When to use**: Linux host, want fastest possible cluster startup with native networking.

**Command**:
```bash
sketcher demo --kind examples/skupper-example-hello-world.yaml
```

**Advantages on Linux**:
- Native container networking (no VM overhead)
- Direct localhost NodePort access (no network-address flag like Colima)
- Lower CPU/memory usage than Minikube

---

### Hybrid: Remote Cluster + Local Cluster

**When to use**: One site on cloud/OpenShift, one local for fast iteration.

**Example**: OpenShift production + local Kind development.

**Setup**:
```bash
# Already logged into OpenShift
oc login https://api.openshift.example.com
oc config view --flatten > ~/.kube/config-openshift
```

**Command** (Sketcher auto-creates local cluster):
```bash
sketcher demo --kind skewer.yaml ~/.kube/config-openshift
```

**Site mapping** (order matters!):
```yaml
sites:
  production:  # First site → first kubeconfig argument
    platform: kubernetes
    namespace: prod
    env:
      KUBECONFIG: ~/.kube/config-openshift
  
  development: # Second site → auto-provisioned Kind cluster
    platform: kubernetes
    namespace: dev
    env:
      KUBECONFIG: ~/.kube/config-local
```

**Manual cluster creation** (optional):
```bash
kind create cluster --name dev
kind get kubeconfig --name dev > ~/.kube/config-dev
sketcher demo skewer.yaml ~/.kube/config-openshift ~/.kube/config-dev
```

---

### Edge: Podman Without Kubernetes

**When to use**: Edge device, no Kubernetes, rootless containers required.

**Prerequisites**: Podman installed (rootless mode).

**Command**:
```bash
sketcher demo examples/podman2podman.yaml
```

**What this creates**:
- Podman namespaces: west, east (in `~/.local/share/skupper/namespaces/`)
- Skupper router containers (no Kubernetes)
- Static link files (no LoadBalancer/NodePort)

**Inspect containers**:
```bash
# List containers in 'west' namespace
podman --namespace west ps

# View Skupper router logs
podman --namespace west logs skupper-router

# Execute command in frontend
podman --namespace west exec -it frontend bash
```

**Limitations**: Single host, services accessed via localhost:PORT only.

---

### Edge: Linux systemd + Kubernetes Cloud

**When to use**: Legacy systemd services need Skupper networking to cloud backend.

**Example configuration**:
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
  - title: Expose systemd service to cloud
    commands:
      onprem:
        - run: skupper connector create legacy-api 8080 --host localhost
```

**Limitations**: Skupper runs as systemd service, services must be at localhost:PORT.

---

### Multi-Cloud: Three Regions (AWS, Azure, GCP)

**When to use**: Test multi-cloud deployments across all three major providers.

**Prerequisites**:
- Kubeconfigs: `~/.kube/config-aws`, `~/.kube/config-azure`, `~/.kube/config-gcp`
- Already authenticated to each cluster

**Command**:
```bash
# Site order matches argument order
sketcher demo multi-cloud.yaml \
  ~/.kube/config-aws \
  ~/.kube/config-azure \
  ~/.kube/config-gcp
```

**Site definition**:
```yaml
sites:
  aws:    # First site → first kubeconfig
    platform: kubernetes
    namespace: us-east-1
    env:
      KUBECONFIG: ~/.kube/config-aws
  
  azure:  # Second site → second kubeconfig
    platform: kubernetes
    namespace: west-europe
    env:
      KUBECONFIG: ~/.kube/config-azure
  
  gcp:    # Third site → third kubeconfig
    platform: kubernetes
    namespace: us-central1
    env:
      KUBECONFIG: ~/.kube/config-gcp
```

---

## Automate Testing

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

Set up automated validation in CI/CD pipelines and git hooks.

### GitHub Actions with Kind+MetalLB

**What you accomplish**: Every push/PR runs full Skupper example tests automatically.

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

---

### GitLab CI with Minikube

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

---

### Pre-commit Hook Validation

**What you accomplish**: Block invalid skewer.yaml commits before they reach CI.

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

---

## Develop Iteratively

Work on Skupper examples with fast feedback loops.

### Add Observability to Running Demo

**What you accomplish**: Install Skupper Network Observer, Prometheus, or load generators without restarting clusters.

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

### Debug Failing Steps

**What you accomplish**: Find the exact command and output causing test failures.

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

### Test Against Remote Staging Cluster

**What you accomplish**: Iterate on local frontend while connecting to real backend in staging.

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

## Production Validation

Test deployment strategies before production rollout.

### Validate GitOps Deployment

**What you accomplish**: Test Skupper custom resources (CRs) before ArgoCD/Flux applies them in production.

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

### Test Blue/Green Deployment

**What you accomplish**: Verify traffic shifting works between blue and green versions before production cutover.

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

### Test Disaster Recovery Failover

**What you accomplish**: Verify DR site takes over when primary fails, before a real disaster.

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

## Troubleshoot Problems

### Resolve Common Issues

**Problem**: NodePort not accessible at localhost on macOS.

**Solution**: 
```bash
# If using Colima:
colima status  # Check if network: true
colima stop
colima start --network-address

# If using Docker Desktop:
# NodePort should work out-of-the-box. Check Docker Desktop is running.
```

---

**Problem**: Minikube LoadBalancer stuck in "Pending".

**Solution**:
```bash
# Terminal 1: Start tunnel (requires sudo)
minikube tunnel

# Terminal 2: Verify LoadBalancer IP assigned
kubectl get svc
```

---

**Problem**: Skupper command fails with "ingress not available".

**Solution**: Check cluster provider and adjust ingress type:

```bash
# Kind with --kind flag → use NodePort
skupper site create west --ingress nodeport --ingress-host localhost

# Kind with --kind-lb OR Minikube → use LoadBalancer (default)
skupper site create west --enable-link-access
```

---

**Problem**: skewer.yaml validation fails.

**Solution**:
```bash
# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('skewer.yaml'))"

# Dry-run generate to find missing fields
skewer generate skewer.yaml --dry-run
```

---

**Problem**: Subnet conflict (192.168.49.0/24 already used).

**Solution**:
```bash
# Remove existing Podman network (might be from another user)
sudo podman network rm minikube
```

---

**Problem**: `sketcher` command not found after installation.

**Solution**:
```bash
# Verify installation
sketcher --help   # Go binary (run, demo, test)
skewer --help     # Python package (generate, resolve)

# If missing, reinstall:
pip install sketcher  # Python tool
# Copy prebuilt binary or build from source:
sudo cp sketcher-linux-x64 /usr/local/bin/sketcher
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

## About This Guide

This documentation uses the **Seven-Action Documentation Model** to organize content around what you need to accomplish:

| Section | Primary Action | Reader Outcome |
|---------|---------------|----------------|
| Quick Start Testing | **Explore** | Try Sketcher in under 60 seconds with minimal setup |
| Choose Your Platform | **Appraise** | Select the right cluster provider for your environment and performance requirements |
| Automate Testing | **Develop** | Integrate Sketcher into CI/CD pipelines and pre-commit hooks |
| Develop Iteratively | **Practice** | Debug failures, extend running demos, test against remote clusters |
| Production Validation | **Develop** | Test GitOps deployments, blue/green rollouts, and disaster recovery before production |
| Troubleshoot Problems | **Troubleshoot** | Diagnose and resolve networking, ingress, and configuration issues |
| Quick Reference | **Remember** | Retrieve commands and decision trees for platform selection |

Each use case leads with **what you accomplish** instead of describing features, so you can find the section that matches your immediate goal.

---

**Last Updated**: 2026-08-11  
**See Also**: `README.md`, `DEVELOPERS.md`, `SCHEMA.md`
