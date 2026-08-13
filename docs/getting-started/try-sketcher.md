# Try Sketcher (5-Minute Start)

**What you'll accomplish**: See a complete Skupper example running across two clusters.

**Prerequisites**: Docker Desktop (macOS) or Docker (Linux) installed and running.

```bash
# 1. Install both tools
pip install sketcher
curl -LO https://github.com/skupperproject/sketcher/releases/latest/download/sketcher-linux-x64
chmod +x sketcher-linux-x64
sudo mv sketcher-linux-x64 /usr/local/bin/sketcher

# 2. Get an example (or use your own)
cd /path/to/your/skupper-example

# 3. Run demo (creates clusters, deploys app, pauses for inspection)
sketcher demo --kind skewer.yaml

# 4. Explore the running application
# - Open URLs shown in demo output
# - Check Skupper network status
# - Inspect pods/services

# 5. Type 'yes' when done to cleanup
```

**What happened**: Sketcher created two Kind clusters, deployed a Skupper network, connected services across clusters, and gave you a working demo environment.

**Next**: See [Installation](installation.md) to set up your own Skupper example project.
