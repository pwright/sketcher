# macOS/minikube Link Failure Fix

## Problem

On macOS with minikube, skupper links fail with "Not Operational" status and show `127.0.0.1` endpoints instead of proper external IPs.

**Root Cause**: When `skupper site create --enable-link-access` runs, the skupper-router LoadBalancer service is created, but the minikube tunnel hasn't fully assigned the external IP yet. The skupper controller falls back to `127.0.0.1` for the access grant endpoints, breaking link connectivity.

## Solution

The fix adds two improvements:

### 1. Increased tunnel initialization time
**File**: `internal/minikube/minikube.go:84`
- Changed from 2 seconds to 5 seconds
- macOS minikube tunnel needs more time to initialize than Linux

### 2. Automatic LoadBalancer wait after site creation
**File**: `internal/executor/executor.go:187-251`
- Detects `skupper site create --enable-link-access` commands
- Automatically waits up to 60 seconds for the skupper-router LoadBalancer to get an external IP
- Logs a warning if the IP isn't ready (instead of failing silently)

## Testing

```bash
# Rebuild
go build -o bin/sketcher cmd/sketcher/main.go

# Test with minikube
./bin/sketcher demo examples/skupper-example-hello-world.yaml

# Verify links are operational
kubectl get links -A -o jsonpath='{.items[*].status.status}'
# Should show: Ready (not Pending)
```

## Technical Details

**Before fix**:
```yaml
spec:
  endpoints:
  - host: 127.0.0.1  # ❌ Wrong - can't connect
    port: "55671"
status:
  status: Pending
  message: Not Operational
```

**After fix**:
```yaml
spec:
  endpoints:
  - host: 10.111.119.0  # ✓ Correct cluster IP
    port: "55671"
status:
  status: Ready
  message: OK
```

## Why This Only Affects macOS

- **Linux**: LoadBalancer IPs assigned immediately by kind/cloud providers
- **macOS/minikube**: LoadBalancer assignment requires `minikube tunnel` process to establish routes, which takes 5-10 seconds
- Without the wait, skupper's access grant creation happens before the IP is available

## Alternative Workarounds

If you still have issues:

1. **Manual approach**: Add `await_ingress` to your YAML:
```yaml
- run: skupper site create west --enable-link-access
- await_ingress: service/skupper-router  # Wait for external IP
```

2. **Pre-start tunnel**: Ensure `sudo minikube tunnel` runs before sketcher
