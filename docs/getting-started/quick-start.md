# Quick Start

Get up and running with Sketcher in minutes.

## Prerequisites

- Docker Desktop (macOS) or Docker (Linux) installed and running
- Python 3.9 or later *(only needed if you want to generate README documentation)*

## Installation

```bash
# Install sketcher
curl https://pwright.github.io/sketcher/install.sh | sh

# Verify
sketcher --help
```

**For example authors** (optional - only needed to generate README.md):

```bash
# Install skewer (Python tool for documentation generation)
pip install sketcher

# Verify both tools
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
