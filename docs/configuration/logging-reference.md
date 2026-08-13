# Logging Reference - Complete Field List

## First Entry: Environment Information

Always the first entry in every log file. Captures the complete system environment.

### Sketcher Information
- **sketcher_version**: Version of sketcher (e.g., "0.2.0")

### System Information
- **os**: Operating system (e.g., "linux", "darwin", "windows")
- **arch**: CPU architecture (e.g., "amd64", "arm64")
- **go_version**: Go runtime version (e.g., "go1.21.5")
- **num_cpu**: Number of CPU cores available
- **hostname**: System hostname
- **user**: Current username (from $USER)
- **home_dir**: User's home directory
- **cwd**: Current working directory when sketcher was invoked

### Kubernetes Configuration
- **kubeconfig_path**: Path to kubeconfig file ($KUBECONFIG or ~/.kube/config)
- **k8s_context**: Current Kubernetes context (from kubectl)

### Minikube (if available)
- **minikube_status**: Minikube host status (e.g., "Running", "Stopped")
- **minikube_profile**: Active minikube profile name

### Kind (if available)
- **kind_clusters**: Array of kind cluster names

### Tool Paths and Versions
For each tool, both the binary path and version are logged (if available):

#### Skupper
- **skupper_path**: Full path to skupper binary
- **skupper_version**: Skupper version string

#### Kubectl
- **kubectl_path**: Full path to kubectl binary
- **kubectl_version**: Kubectl version string

#### Podman
- **podman_path**: Full path to podman binary
- **podman_version**: Podman version string

#### Docker
- **docker_path**: Full path to docker binary
- **docker_version**: Docker server version

#### Skewer (Python)
- **skewer_path**: Full path to skewer binary
- **skewer_version**: Skewer (Python) version string

## Second Entry: Execution Context

Always the second entry. Captures how sketcher is being run.

### Run Configuration
- **run_type**: Type of run ("demo", "test", or "run")
- **exec_mode**: Execution mode:
  - `"kind"` - Running with Kind
  - `"kind-metallb"` - Running with Kind + MetalLB
  - `"minikube"` - Running with Minikube
  - `"native"` - Running with native kubeconfigs
  - `"unknown"` - No Kubernetes detected

### File Locations
- **yaml_file**: Path to the skewer.yaml being executed
- **work_dir**: Working directory for this run (where kubeconfigs, tokens, etc. are stored)
- **log_dir**: Directory where logs are stored ("/tmp/sk-logs")
- **log_file**: Full path to this log file

## Why This Information Matters

### Debugging
- **Tool paths**: Confirm which binaries are being used (important when multiple versions installed)
- **Versions**: Identify version compatibility issues
- **Work directory**: Find kubeconfigs, tokens, and other generated files
- **Kubernetes context**: Verify running against correct cluster

### Reproducibility
- **System info**: Reproduce issues on similar systems
- **Tool versions**: Match exact environment for bug reports
- **Execution mode**: Understand cluster provisioning method

### Support
- **Complete environment snapshot**: Attach log file to bug reports
- **Version matrix**: Confirm supported version combinations
- **File locations**: Help locate generated artifacts

## Example: Complete First Two Entries

```json
{"timestamp":"2026-08-12T14:30:22Z","type":"info","message":"Environment","context":{"sketcher_version":"0.2.0","os":"linux","arch":"amd64","go_version":"go1.21.5","num_cpu":8,"hostname":"dev-machine","user":"developer","home_dir":"/home/developer","cwd":"/home/developer/projects/skupper-examples/hello-world","kubeconfig_path":"/home/developer/.kube/config","k8s_context":"minikube","minikube_status":"Running","minikube_profile":"skewer","skupper_path":"/usr/local/bin/skupper","skupper_version":"1.8.0","kubectl_path":"/usr/bin/kubectl","kubectl_version":"v1.28.3","docker_path":"/usr/bin/docker","docker_version":"24.0.7","skewer_path":"/home/developer/.local/bin/skewer","skewer_version":"1.4.0"}}
{"timestamp":"2026-08-12T14:30:22Z","type":"info","message":"Execution context","context":{"run_type":"demo","exec_mode":"minikube","yaml_file":"skewer.yaml","work_dir":"/tmp/sketcher","log_dir":"/tmp/sk-logs","log_file":"/tmp/sk-logs/skewer-20260812-143022.log"}}
```

## Querying Environment Information

Extract specific environment details with jq:

```bash
# Get sketcher version
jq -r 'select(.message == "Environment") | .context.sketcher_version' log.json

# Get all tool versions
jq 'select(.message == "Environment") | .context | with_entries(select(.key | endswith("_version")))' log.json

# Get all tool paths
jq 'select(.message == "Environment") | .context | with_entries(select(.key | endswith("_path")))' log.json

# Get execution mode
jq -r 'select(.message == "Execution context") | .context.exec_mode' log.json

# Get complete environment as pretty JSON
jq 'select(.message == "Environment") | .context' log.json
```
