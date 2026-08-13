# Demo and Test Modes

Sketcher provides two execution modes depending on whether you need interactive exploration or automated validation.

## Demo Mode: Interactive Exploration

Demo mode executes all steps, then pauses before cleanup so you can inspect and interact with the running application.

When you run `sketcher demo skewer.yaml`, after all steps complete successfully, Sketcher displays connection information and waits:

```
Demo time!

Sites:

  west: export KUBECONFIG=/tmp/sketcher-xyz/.kube/config-west
  east: export KUBECONFIG=/tmp/sketcher-xyz/.kube/config-east

Frontend URL:     http://localhost:8080/
Console URL:      https://skupper-west.example.com:8010/
Console user:     admin
Console password: abc123xyz

Are you done (yes)?
```

This allows you to:

- Test the application manually
- Inspect Skupper network status
- Try different configurations
- Verify expected behavior

When you're finished, type `yes` to clean up and exit.

### Running a Demo

```bash
# Basic demo
sketcher demo skewer.yaml

# With cluster provider options
sketcher demo --kind skewer.yaml        # Fast startup with Kind
sketcher demo --kind-lb skewer.yaml     # Kind with LoadBalancer

# With debugging flags
sketcher demo skewer.yaml --verbose     # Show debug output
sketcher demo skewer.yaml --debug       # Debug output on failure
sketcher demo skewer.yaml --quiet       # Suppress progress messages
```

## Test Mode: Automated Validation

Test mode runs all steps automatically, generates documentation, validates output, then cleans up. Perfect for CI/CD pipelines.

```bash
# Run full automated test (no pause, auto-cleanup)
sketcher test skewer.yaml

# With cluster provider options
sketcher test --kind-lb skewer.yaml  # Fast CI/CD testing
```

Test mode automatically:

1. Generates the README (verifies documentation is up to date)
2. Discovers all `skewer-extend-*.yaml` files in the current directory
3. Concatenates their steps to the base `skewer.yaml` steps
4. Runs all steps in sequence
5. Cleans up automatically when complete

!!! tip
    If no `skewer-extend-*.yaml` files exist, `test` runs only the base `skewer.yaml` (backward compatible).

## Choosing Between Modes

| Use Case | Mode | Command |
|----------|------|---------|
| Local development | Demo | `sketcher demo skewer.yaml` |
| Debugging issues | Demo | `sketcher demo skewer.yaml --verbose` |
| Manual testing | Demo | `sketcher demo skewer.yaml` |
| CI/CD pipeline | Test | `sketcher test skewer.yaml` |
| Automated validation | Test | `sketcher test skewer.yaml` |
| Pre-commit checks | Test | `sketcher test skewer.yaml` |

## Next Steps

- Learn how to [Extend Running Demos](extending-demos.md)
- Explore [Cluster Providers](cluster-providers.md) for different environments
- See [Use Cases](use-cases.md) for comprehensive workflows
