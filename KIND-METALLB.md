# Kind with MetalLB Support (`--kind-lb`)

## Overview

Sketcher now supports **Kind with MetalLB** via the `--kind-lb` flag, providing LoadBalancer ingress on Kind clusters. This combines Kind's speed advantages with LoadBalancer compatibility.

## Quick Start

```bash
# Demo with MetalLB
sketcher demo skewer.yaml --kind-lb

# Test with MetalLB
sketcher test skewer.yaml --kind-lb
```

## What Gets Installed

When you use `--kind-lb`, Sketcher automatically:

1. Creates a Kind cluster (same as `--kind`)
2. Installs MetalLB v0.14.5 from official manifests
3. Detects the Kind Docker network subnet
4. Configures an IPAddressPool with safe IP range (e.g., `172.18.255.200-172.18.255.250`)
5. Enables L2Advertisement for the IP pool

All of this happens automatically - no manual configuration required.

## How It Works

### Docker Network Detection

MetalLB needs an IP range from your Docker network. Sketcher automatically:

```bash
# Detects Kind network subnet
docker network inspect kind --format '{{ (index .IPAM.Config 0).Subnet }}'
# Example output: 172.18.0.0/16

# Calculates safe IP range (high end of subnet to avoid conflicts)
# Result: 172.18.255.200-172.18.255.250
```

### MetalLB Configuration

Sketcher applies this configuration automatically:

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: sketcher-pool
  namespace: metallb-system
spec:
  addresses:
  - 172.18.255.200-172.18.255.250
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: sketcher-advertisement
  namespace: metallb-system
spec:
  ipAddressPools:
  - sketcher-pool
```

## Skupper Configuration

With `--kind-lb`, use **standard LoadBalancer commands** - no special flags needed:

```yaml
# NO --ingress nodeport needed!
commands:
  west:
    - run: skupper site create west --enable-link-access
  east:
    - run: skupper site create east
```

This is identical to Minikube configuration.

## Comparison Matrix

| Flag | Cluster | Ingress Type | MetalLB | Skupper Config | Speed | Use Case |
|------|---------|--------------|---------|----------------|-------|----------|
| (none) | Minikube | LoadBalancer | No | Standard | Slower | Production-like testing |
| `--kind` | Kind | NodePort | No | `--ingress nodeport` | Fast | CI/CD, port mapping OK |
| `--kind-lb` | Kind | LoadBalancer | Yes | Standard | Fast | CI/CD, need LoadBalancer |

## When to Use `--kind-lb`

✅ **Use `--kind-lb` when:**
- You need LoadBalancer ingress for compatibility
- You want Kind's speed (faster than Minikube)
- Running in CI/CD pipelines
- Testing examples that assume LoadBalancer
- You want to avoid modifying Skupper commands for NodePort

✅ **Use `--kind` (NodePort) when:**
- You're comfortable with NodePort configuration
- Smaller IP footprint needed
- Don't need full LoadBalancer simulation
- Simple port-mapped services sufficient

✅ **Use Minikube (default) when:**
- You need the most production-like environment
- Minikube is already your standard tool
- Don't need the speed advantage of Kind

## Technical Details

### Installation Process

1. **Create Kind cluster** - Standard cluster with port mappings
2. **Install MetalLB** - Applies manifest from `https://raw.githubusercontent.com/metallb/metallb/v0.14.5/config/manifests/metallb-native.yaml`
3. **Wait for ready** - Waits up to 90 seconds for MetalLB pods
4. **Detect subnet** - Inspects Kind Docker network
5. **Configure IP pool** - Creates IPAddressPool with `.255.200-.255.250` range
6. **Enable L2 mode** - Creates L2Advertisement resource

### IP Range Calculation

The IP range is calculated to avoid conflicts with Kind containers:

```go
// For subnet 172.18.0.0/16
startIP := "172.18.255.200"
endIP := "172.18.255.250"

// For subnet 192.168.207.0/24
startIP := "192.168.255.200"
endIP := "192.168.255.250"
```

This provides 51 IP addresses for LoadBalancer services, which is sufficient for typical Skupper testing scenarios.

### MetalLB Version

Currently using **MetalLB v0.14.5** (latest stable as of implementation). This can be updated by changing the manifest URL in `internal/kind/kind.go`.

## Troubleshooting

### MetalLB pods not starting

```bash
# Check MetalLB status
kubectl --namespace metallb-system get pods

# Check controller logs
kubectl --namespace metallb-system logs -l app=metallb,component=controller

# Check speaker logs
kubectl --namespace metallb-system logs -l app=metallb,component=speaker
```

### LoadBalancer stuck in Pending

```bash
# Check IP pool
kubectl --namespace metallb-system get ipaddresspools

# Check L2Advertisement
kubectl --namespace metallb-system get l2advertisements

# Verify IP range doesn't conflict
docker network inspect kind
```

### Wrong IP range assigned

This usually means a conflict with existing Docker containers. The subnet detection uses the first available IPAM config. If you have multiple networks or complex Docker setups, the auto-detection may need adjustment.

## Benefits Over Plain Kind

- ✅ **No Skupper command changes** - Use standard LoadBalancer syntax
- ✅ **Better compatibility** - Works with examples expecting LoadBalancer
- ✅ **Faster than Minikube** - Kind startup is typically 2-3x faster
- ✅ **Automatic setup** - MetalLB installed and configured automatically
- ✅ **Isolated IPs** - Each LoadBalancer service gets unique external IP
- ✅ **CI/CD friendly** - Fast, repeatable, no manual tunnel needed

## Example Workflow

```bash
# Start demo with MetalLB
sketcher demo examples/skupper-example-hello-world.yaml --kind-lb

# Kind cluster created with MetalLB
# MetalLB IP range: 172.18.255.200-172.18.255.250

# Deploy Skupper sites (standard commands)
skupper site create west --enable-link-access
skupper site create east

# LoadBalancer services get IPs automatically
kubectl get svc -A | grep LoadBalancer
# skupper-router LoadBalancer 172.18.255.200 ...

# Services accessible at assigned IPs
curl http://172.18.255.200:8080
```

## Files Modified

- `internal/kind/kind.go` - Added `UseMetalLB` field and `installMetalLB()` function
- `internal/cli/cli.go` - Added `--kind-lb` flag to `demo` and `test` commands
- `README.md` - Documented `--kind-lb` option and usage
- `.claude/SKUPPER.md` - Updated Skupper configuration guidance
- `KIND-METALLB.md` - This documentation file

## References

- [MetalLB Official Installation](https://metallb.universe.tf/installation/)
- [How to Install MetalLB on Kind for Local Development](https://oneuptime.com/blog/post/2026-02-20-metallb-kind-local-development/view)
- [Automatically set MetalLB IP addresses with kind](https://michaelheap.com/metallb-ip-address-pool/)
- [MetalLB and KinD: Loads Balanced Locally](https://medium.com/@tylerauerbeck/metallb-and-kind-loads-balanced-locally-1992d60111d8)
- [Kind cluster LB with metallb](https://github.com/kubernetes-sigs/kind/issues/3560)

---

**Sketcher with Kind + MetalLB: Fast local clusters with full LoadBalancer support!** 🚀
