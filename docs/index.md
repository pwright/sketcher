# Sketcher

**Automate Skupper example documentation and testing from a single YAML file.**

## What You Can Accomplish

With Sketcher, you can:

- **Generate consistent documentation** - Write steps once in YAML, get formatted README.md with copy-paste commands
- **Test examples automatically** - Run full multi-cluster demos in CI/CD without manual setup
- **Demo interactively** - Pause before cleanup to explore running applications and Skupper networking
- **Validate before deployment** - Test Skupper configurations locally before pushing to production
- **Work across platforms** - Same YAML runs on Kubernetes, Podman, Docker, and systemd

[Get Started](getting-started/installation.md){ .md-button .md-button--primary }
[Try in 5 Minutes](getting-started/quick-start.md){ .md-button }

## How It Works

Sketcher uses two command-line tools:

- **`skewer`** (Python) - Processes YAML and generates documentation
- **`sketcher`** (Go) - Executes steps, provisions clusters, runs tests

Both read the same `skewer.yaml` file describing your Skupper example's sites, steps, and commands.

## Quick Example

```bash
# Install
pip install sketcher
curl -LO https://github.com/skupperproject/sketcher/releases/latest/download/sketcher-linux-x64

# Run demo
sketcher demo --kind skewer.yaml
```

## Key Features

<div class="grid cards" markdown>

- :material-file-document: **Documentation Generation**

    Generate consistent README.md from YAML configuration

- :material-test-tube: **Automated Testing**

    Run full multi-cluster tests in CI/CD pipelines

- :material-kubernetes: **Multi-Platform**

    Kubernetes, Podman, Docker, and systemd support

- :material-console: **Interactive Demos**

    Pause execution to explore running applications

- :material-code-json: **JSON Schema Validation**

    Catch errors before running with schema validation

- :material-update: **Migration Support**

    Migrate from legacy Skewer with resolver tool

</div>

## Documentation Organization

This documentation follows a user-journey structure to help you find what you need:

- **Getting Started** - Install and try Sketcher in under 5 minutes
- **User Guide** - Write YAML, run demos, test examples, choose platforms
- **Configuration** - Schema validation and logging
- **Migration** - Migrate from legacy Skewer
- **Development** - Contribute to Sketcher
- **Troubleshooting** - Common issues and solutions
