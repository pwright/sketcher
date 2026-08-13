# Common Issues

Solutions to frequently encountered problems when running Sketcher.

## Subnet is Already Used

**Error**:

```console
plano: notice: Starting Minikube
plano: notice: Running command 'minikube start -p skewer --auto-update-drivers false'
* Creating podman container (CPUs=2, Memory=16000MB) ...- E0229 05:44:29.821273   12224 network_create.go:113] error while trying to create podman network skewer 192.168.49.0/24

Error: subnet 192.168.49.0/24 is already used on the host or by another config
```

**Solution**:

Remove the existing Podman network. Note that it might belong to another user on the host.

```shell
sudo podman network rm minikube
```

## Sketcher Command Not Found After Installation

**Error**: `python -m sketcher` fails with "No module named sketcher"

**Solution**:

Ensure you installed Sketcher correctly:

```bash
cd /path/to/sketcher
pip install sketcher
```

Verify installation:

```bash
skewer --help
sketcher --help
```

If the Go tool (`sketcher`) is not found, ensure it's in your PATH:

```bash
# Check if installed
which sketcher

# If not found, copy binary to PATH
sudo cp sketcher-linux-x64 /usr/local/bin/sketcher
chmod +x /usr/local/bin/sketcher
```

## Resolver Fails on Old Skewer YAML

**Issue**: The `skewer resolve` command fails on very old Skewer YAML files with unprefixed step names.

**Solution**:

1. **Update to modern format**: Manually update the YAML to use prefixed step names
2. **Use common patterns**: Replace old standard steps with [common patterns](../user-guide/common-patterns.md)
3. **Check compatibility**: See the [migration guide](../migration/from-skewer.md) for details

**Migration success rates**:
- ✅ 100% success on 2024+ examples
- ⚠️ 63% success overall (failures only on very old files)

## Skupper `init` Command Not Found

**Error**: `skupper init` fails with "unknown command"

**Solution**:

Sketcher uses Skupper v2 syntax. The old `skupper init` command from v1 is deprecated.

Use `skupper site create` instead:

```yaml
# OLD (v1 - doesn't work)
- run: skupper init --site-name west

# NEW (v2 - correct)
- run: skupper site create west --enable-link-access
```

## Port Already in Use

**Error**: Cannot bind to port (e.g., 8080) because it's already in use.

**Solution**:

Find and kill the process using the port:

```bash
# Find the process
lsof -i :8080

# Kill it
kill -9 <PID>
```

Or use a different port in your configuration.

## Kind Requires Docker Desktop on macOS

**Error**: Kind fails to start on macOS

**Solution**:

Kind requires Docker Desktop or Colima to be running on macOS:

**Option 1: Docker Desktop** (works out-of-the-box)
```bash
# Ensure Docker Desktop is running
# Then run your sketcher command
sketcher demo --kind skewer.yaml
```

**Option 2: Colima**
```bash
# Start Colima with network access
colima start --network-address

# Then run your sketcher command
sketcher demo --kind skewer.yaml
```

## Need More Help?

- Check [Viewing Logs](viewing-logs.md) for debugging information
- See [Use Cases](../user-guide/use-cases.md) for platform-specific workflows
- Review [Cluster Providers](../user-guide/cluster-providers.md) for environment options
