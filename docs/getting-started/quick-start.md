# Quick Start

Get up and running with Sketcher in minutes.

## Prerequisites

- Docker Desktop (macOS) or Docker (Linux) installed and running
- Python 3.9 or later
- Go 1.23 or later (if building from source)

## Installation

```bash
# Install skewer (Python tool)
pip install sketcher

# Install sketcher (Go tool)
curl -LO https://github.com/skupperproject/sketcher/releases/latest/download/sketcher-linux-x64
chmod +x sketcher-linux-x64
sudo mv sketcher-linux-x64 /usr/local/bin/sketcher

# Verify
skewer --help
sketcher --help
```

## Run Your First Demo

```bash
# Navigate to a Skupper example directory
cd /path/to/your/skupper-example

# Run interactive demo
sketcher demo --kind skewer.yaml
```

The demo will:

1. Create two Kind clusters (~30 seconds)
2. Deploy your Skupper example
3. Pause for inspection
4. Clean up when you're ready

## What's Next?

- **[Try Sketcher in 5 Minutes](try-sketcher.md)** - Detailed walkthrough
- **[Installation Guide](installation.md)** - Full installation options
- **[Writing skewer.yaml](../user-guide/writing-skewer-yaml.md)** - Create your own examples
- **[Use Cases](../user-guide/use-cases.md)** - Platform-specific workflows
