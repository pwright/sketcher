# Logging

Every `sketcher demo`, `sketcher test`, and `sketcher run` execution automatically generates a detailed log file in the work directory. This log file captures all execution details to help with debugging and understanding what happened during a run.

## Log File Location

Log files are automatically created in the work directory with the naming pattern:
```
sketcher-{run-type}-{timestamp}.log
```

For example:
- `sketcher-demo-20260812-143022.log`
- `sketcher-test-20260812-144530.log`
- `sketcher-run-20260812-145601.log`

At the end of each run, sketcher will print the log file path:
```
Log file: /tmp/sketcher-xyz123/sketcher-demo-20260812-143022.log
```

## Log Format

Logs are written in **JSON Lines** format (one JSON object per line), making them both machine-parseable and human-readable with the viewer.

Each log entry includes:
- `timestamp`: ISO 8601 timestamp
- `type`: Entry type (step, command, wait, error, info, step_complete)
- Additional fields specific to the entry type

### Entry Types

#### `info`
General information about the run:
```json
{
  "timestamp": "2026-08-12T14:30:22Z",
  "type": "info",
  "message": "Run started",
  "context": {
    "run_type": "demo",
    "yaml_file": "skewer.yaml",
    "work_dir": "/tmp/sketcher-xyz123"
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

Logs are stored in the work directory:
- For `demo` mode: Logs persist in the work directory until you run `sketcher clean` or delete manually
- For `test` mode: Logs persist in the temporary work directory (usually `/tmp/sketcher-*`)
- For `run` mode: Logs persist in the specified or temporary work directory

To preserve logs from temporary directories, copy them before the work directory is cleaned up.
