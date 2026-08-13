# Logging

Every `sketcher demo`, `sketcher test`, and `sketcher run` execution automatically generates a detailed log file in the work directory. This log file captures all execution details to help with debugging and understanding what happened during a run.

## Log File Location

Log files are automatically created in `/tmp/sk-logs/` with the naming pattern:
```
sketcher-{run-type}-{timestamp}.log
```

For example:
- `sketcher-demo-20260812-143022.log`
- `sketcher-test-20260812-144530.log`
- `sketcher-run-20260812-145601.log`

At the end of each run, sketcher will print the log file path:
```
Log file: /tmp/sk-logs/sketcher-demo-20260812-143022.log
```

**Note**: Logs are stored separately from work directories to prevent deletion during cleanup. This means logs persist across multiple runs and are not removed when demo work directories are cleaned up.

## Log Format

Logs are written in **JSON Lines** format (one JSON object per line), making them both machine-parseable and human-readable with the viewer.

Each log entry includes:
- `timestamp`: ISO 8601 timestamp
- `type`: Entry type (step, command, wait, error, info, step_complete)
- Additional fields specific to the entry type

### Entry Types

#### `info`
General information about the run. The first two entries are always:

**First entry - Environment information:**
```json
{
  "timestamp": "2026-08-12T14:30:22Z",
  "type": "info",
  "message": "Environment",
  "context": {
    "sketcher_version": "0.2.0",
    "os": "linux",
    "arch": "amd64",
    "go_version": "go1.21.5",
    "num_cpu": 8,
    "hostname": "myhost",
    "user": "developer",
    "home_dir": "/home/developer",
    "cwd": "/home/developer/projects/my-demo",
    "kubeconfig_path": "/home/developer/.kube/config",
    "k8s_context": "minikube",
    "minikube_status": "Running",
    "minikube_profile": "skewer",
    "skupper_path": "/usr/local/bin/skupper",
    "skupper_version": "1.8.0",
    "kubectl_path": "/usr/bin/kubectl",
    "kubectl_version": "v1.28.3",
    "docker_path": "/usr/bin/docker",
    "docker_version": "24.0.7",
    "skewer_path": "/usr/local/bin/skewer",
    "skewer_version": "1.4.0"
  }
}
```

**Second entry - Execution context:**
```json
{
  "timestamp": "2026-08-12T14:30:22Z",
  "type": "info",
  "message": "Execution context",
  "context": {
    "run_type": "demo",
    "exec_mode": "minikube",
    "yaml_file": "skewer.yaml",
    "work_dir": "/tmp/sketcher",
    "log_dir": "/tmp/sk-logs",
    "log_file": "/tmp/sk-logs/skewer-20260812-143022.log"
  }
}
```

#### `step`
Start of a step:
```json
{
  "timestamp": "2026-08-12T14:30:23Z",
  "type": "step",
  "step_number": 1,
  "step_name": "Configure the router network"
}
```

#### `command`
Command execution:
```json
{
  "timestamp": "2026-08-12T14:30:24Z",
  "type": "command",
  "site": "public",
  "command": "skupper site create --enable-link-access public",
  "context": {
    "background": false
  }
}
```

#### `wait`
Wait operations (resource, ingress, port, etc.):
```json
{
  "timestamp": "2026-08-12T14:30:25Z",
  "type": "wait",
  "wait_type": "resource",
  "wait_target": "deployment/skupper-router",
  "wait_timeout": 300,
  "site": "public"
}
```

#### `step_complete`
Step completion with duration:
```json
{
  "timestamp": "2026-08-12T14:30:30Z",
  "type": "step_complete",
  "step_number": 1,
  "step_name": "Configure the router network",
  "duration": 7.234
}
```

#### `error`
Errors encountered:
```json
{
  "timestamp": "2026-08-12T14:30:35Z",
  "type": "error",
  "error": "command failed: exit status 1",
  "context": {
    "step": "step 2 'Deploy the application'"
  }
}
```

## Viewing Logs

### Human-Readable View

Use the `view-log` command to view logs in a human-readable format:

```bash
sketcher view-log /tmp/sketcher-xyz123/sketcher-demo-20260812-143022.log
```

Output:
```
[14:30:22] INFO: Run started
  run_type: demo
  yaml_file: skewer.yaml
  work_dir: /tmp/sketcher-xyz123

[14:30:23] STEP 1: Configure the router network
───────────────────────────────────────────────

[14:30:24] CMD [public]: skupper site create --enable-link-access public
[14:30:25] WAIT [public]: resource for deployment/skupper-router (timeout: 300s)
[14:30:30] ✓ Step 1 completed in 7.23s
```

### Machine Processing

Since logs are JSON Lines format, you can easily process them with standard tools:

```bash
# Extract all commands
jq -r 'select(.type == "command") | .command' sketcher-demo-20260812-143022.log

# Find all waits
jq 'select(.type == "wait")' sketcher-demo-20260812-143022.log

# Calculate total runtime
jq -r 'select(.type == "info" and .message == "Run completed") | .context.total_duration_seconds' sketcher-demo-20260812-143022.log

# Find errors
jq 'select(.type == "error")' sketcher-demo-20260812-143022.log

# Get step timings
jq -r 'select(.type == "step_complete") | "\(.step_number) \(.step_name): \(.duration)s"' sketcher-demo-20260812-143022.log
```

## What Gets Logged

The logger captures:

1. **Run context**: Start time, run type (demo/test/run), YAML file, work directory
2. **Each step**: Step number, title, start time
3. **Every command**: Site, command string, whether it's a background process
4. **All waits**: Type (resource, ingress, port, console, http), target, timeout, site
5. **Step completion**: Duration for each step
6. **Errors**: Error message with context
7. **Run summary**: Total duration, number of steps executed

## Debugging with Logs

When debugging a failed run:

1. **Find the log file** - printed at the end of the run or in the work directory
2. **View with `sketcher view-log`** to see the execution flow
3. **Look for the error entry** to see what failed
4. **Check preceding commands** to see what led to the failure
5. **Review wait operations** to see if timeouts occurred
6. **Check step timings** to identify slow operations

Example debugging workflow:
```bash
# View the full log
sketcher view-log /tmp/sketcher-xyz123/sketcher-test-20260812-143022.log

# Find the error
jq 'select(.type == "error")' sketcher-test-20260812-143022.log

# See what commands ran before the error
jq -r 'select(.type == "command") | "\(.timestamp) [\(.site)] \(.command)"' sketcher-test-20260812-143022.log | tail -5

# Check for slow waits
jq -r 'select(.type == "wait") | "\(.wait_type) \(.wait_target) (timeout: \(.wait_timeout)s)"' sketcher-test-20260812-143022.log
```

## Log Retention

Logs are stored in `/tmp/sk-logs/`:
- **All modes** (demo/test/run): Logs persist in `/tmp/sk-logs/` and are never automatically deleted
- Logs survive work directory cleanup (when starting new demos)
- Logs are only removed when `/tmp` is cleaned by the OS (typically on reboot)
- Multiple runs accumulate logs in the same directory

To clean up old logs:
```bash
# Use sketcher's built-in clean command
sketcher clean --logs

# Or manually remove specific logs
rm /tmp/sk-logs/*.log

# Remove logs older than 7 days
find /tmp/sk-logs -name "*.log" -mtime +7 -delete

# Remove logs from a specific run type
rm /tmp/sk-logs/sketcher-demo-*.log
```
