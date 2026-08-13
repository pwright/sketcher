# Cluster Providers

By default, Sketcher starts a local Minikube instance automatically. Choose a different provider based on your performance needs and environment.

## Cluster Provider Comparison

| Provider | Flag | Ingress Type | Startup | Resource Usage | Best For |
|----------|------|--------------|---------|----------------|----------|
| **Minikube** | (default) | LoadBalancer | Slower | Higher | Full compatibility testing |
| **Kind** | `--kind` | NodePort | Faster | Lower | CI/CD, quick iterations |
| **Kind + MetalLB** | `--kind-lb` | LoadBalancer | Fast | Lower | Best of both worlds |

### Minikube (Default)

- Uses LoadBalancer ingress
- Slower startup
- Higher resource usage
- Full compatibility with standard Skupper configurations

### Kind

- Uses NodePort ingress
- Faster startup (~30 seconds)
- Lower resource usage
- Better for CI/CD pipelines
- **macOS prerequisite**: Requires Docker Desktop or Colima
  - Docker Desktop: Works out-of-the-box
  - Colima: Start with `colima start --network-address` for direct NodePort access

### Kind with MetalLB

- Uses LoadBalancer ingress like Minikube
- Automatically installs and configures MetalLB
- No need for `--ingress nodeport` in Skupper commands
- Best of both: Kind's speed + LoadBalancer ingress compatibility

## Configuring Skupper for Different Providers

The Skupper configuration depends on which cluster provider and ingress type you're using:

### Minikube (default) - LoadBalancer Ingress

```yaml
- run: skupper site create west --enable-link-access
```

### Kind with `--kind-lb` Flag - LoadBalancer via MetalLB

Same as Minikube:

```yaml
- run: skupper site create west --enable-link-access
```

### Kind with `--kind` Flag - NodePort Ingress

```yaml
- run: skupper site create west --ingress nodeport --ingress-host localhost --enable-link-access
```

## When to Use `--ingress nodeport`

- ✅ Only needed with `--kind` flag (NodePort mode)
- ❌ NOT needed with `--kind-lb` flag (MetalLB provides LoadBalancer)
- ❌ NOT needed with default Minikube

### Example for Kind with NodePort (`--kind`)

```yaml
commands:
  west:
    - run: skupper site create west --ingress nodeport --ingress-host localhost --enable-link-access
  east:
    - run: skupper site create east --ingress nodeport --ingress-host localhost
```

!!! warning
    This project uses Skupper v2 syntax. The old `skupper init` command from v1 is deprecated and no longer works. Always use `skupper site create`.

## Using Remote Clusters

Kubeconfigs are assigned to Kubernetes sites **in the order the sites are defined** in `skewer.yaml`. For example:

```yaml
sites:
  west:
    platform: kubernetes
    namespace: west
    env:
      KUBECONFIG: ~/.kube/config-west
  east:
    platform: kubernetes
    namespace: east
    env:
      KUBECONFIG: ~/.kube/config-east
```

`west` is the first Kubernetes site and `east` is the second.

### Example: Remote OpenShift + Local Minikube

To run with a remote OpenShift cluster for `west` and a local Minikube instance for `east`:

1. First start Minikube and export its kubeconfig:

```bash
minikube start -p east
minikube -p east kubeconfig > ~/.kube/config-east-minikube
```

2. Then pass the kubeconfigs in site order (west first, east second):

```bash
sketcher demo skewer.yaml ~/.kube/config-west-openshift ~/.kube/config-east-minikube
```

Or equivalently for `run`:

```bash
sketcher run skewer.yaml ~/.kube/config-west-openshift ~/.kube/config-east-minikube
```

!!! note
    The provided kubeconfigs override the paths in `skewer.yaml` at runtime — the `skewer.yaml` file itself is not modified. Each kubeconfig must already be authenticated and have the correct namespace context set before running.

## Next Steps

- See [Demo and Test Modes](demo-test-modes.md) for execution options
- Explore [Use Cases](use-cases.md) for platform-specific workflows
- Learn about [Extending Demos](extending-demos.md) for advanced testing
