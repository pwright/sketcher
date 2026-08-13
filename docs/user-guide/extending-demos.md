# Extending Running Demos

Add observability, scaling, or chaos testing to a running demo without restarting clusters. Sketcher provides two complementary approaches.

## Approach 1: Interactive Extensions (`demo-extend`)

Attach to a running demo and execute additional scenarios while keeping clusters and services active. Perfect for iterative testing, adding observability, or exploring different configurations.

### Usage

In one terminal, start the demo:

```console
$ sketcher demo skewer.yaml
```

The demo will execute all setup steps and then pause, displaying connection information.

In a separate terminal, run additional test scenarios:

```console
$ sketcher demo-extend skewer-extend-observability.yaml
$ sketcher demo-extend skewer-extend-scaling.yaml
$ sketcher demo-extend skewer-extend-chaos.yaml
```

Each `demo-extend` invocation:

- Attaches to the running demo's environment (same kubeconfigs, namespaces, clusters)
- Executes the steps defined in the extension YAML file
- Exits while leaving the demo running for further testing

### Extension YAML Format

The extension YAML files follow the same format as `skewer.yaml` but only require a `steps` section (sites are inherited from the running demo):

```yaml
# skewer-extend-observability.yaml
title: Add Skupper Network Observer
steps:
  - title: Install Skupper Network Observer
    preamble: |
      The Network Observer provides a web console for monitoring
      your Skupper network in real time.
    commands:
      west:
        - run: helm install skupper-network-observer oci://quay.io/skupper/helm/network-observer --version 2.2.1
        - run: kubectl create route passthrough skupper-console --service=skupper-network-observer --port=https
        - run: kubectl get secret skupper-network-observer-auth -o jsonpath='{.data.htpasswd}' | base64 -d
          output: |
            admin:password123
```

### Common Use Cases for Demo Extensions

- Adding observability tools (Network Observer, Prometheus)
- Testing scaling scenarios
- Demonstrating optional features
- Chaos/failure testing
- Performance testing variations

When finished, return to the first terminal and type `yes` to clean up and exit.

## Approach 2: Batch Testing (`test` with extensions)

The `test` command automatically discovers and runs all test scenarios in a single batch execution. Ideal for CI/CD pipelines.

### Usage

```console
$ sketcher test skewer.yaml
```

This command:

1. Generates the README (verifies documentation is up to date)
2. Discovers all `skewer-extend-*.yaml` files in the current directory
3. Concatenates their steps to the base `skewer.yaml` steps
4. Runs all steps in sequence on Minikube
5. Cleans up automatically when complete

!!! note
    If no `skewer-extend-*.yaml` files exist, `test` runs only the base `skewer.yaml` (backward compatible).

### Example Project Structure

```
my-skupper-example/
  skewer.yaml                      # Base: setup, deploy app, basic smoke test
  skewer-extend-observability.yaml # Add Network Observer
  skewer-extend-scaling.yaml       # Test scaling scenarios
  skewer-extend-failure.yaml       # Chaos/failure testing
  README.md                        # Generated documentation
```

### GitHub Actions Example

```yaml
name: Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Sketcher
        run: |
          pip install pyyaml
          pip install -e /path/to/sketcher
      - name: Run all tests
        run: sketcher test skewer.yaml
```

The `test` command runs all extension files automatically, in alphabetical order.

## When to Use Each Approach

| Scenario | Use | Command |
|----------|-----|---------|
| Interactive development | `demo` + `demo-extend` | Multiple terminals |
| Debugging issues | `demo` + `demo-extend` | Interactive exploration |
| Automated CI/CD | `test` | Single command |
| Comprehensive test runs | `test` | Batch execution |

## Next Steps

- Learn about [Cluster Providers](cluster-providers.md) for different environments
- See [Demo and Test Modes](demo-test-modes.md) for execution details
- Explore [Use Cases](use-cases.md) for comprehensive workflows
