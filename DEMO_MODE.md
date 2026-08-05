# Demo Mode Implementation

## Overview

Demo mode allows you to run a Skupper example, pause at the end for interactive exploration, and then extend it with additional steps without tearing down the infrastructure.

## How It Works

### 1. Starting a Demo

```bash
./sketcher-go demo examples/skupper-example-hello-world.yaml
```

This will:
1. Start Minikube (or Kind with `--kind`)
2. Start the Minikube tunnel
3. Run all example steps **except** `cleaning_up`
4. **Save demo context** to `.demo-context.json`
5. **Display demo information**:
   - Site kubeconfig paths
   - Frontend URL (if available)
   - Console URL and credentials (if available)
6. **Pause and wait** for user confirmation

### 2. Demo Display

When paused, you'll see:

```
✓ step 9 'Access the frontend service'

Demo time!

Sites:

  west: export KUBECONFIG=/tmp/sketcher/config-west
  east: export KUBECONFIG=/tmp/sketcher/config-east

Frontend URL:     http://localhost:8080/

Console URL:      https://10.96.0.123:8010/
Console user:     admin
Console password: abc123xyz

Are you done (yes)? 
```

### 3. Exploring the Demo

While paused, you can:

- **Access the frontend**: Open http://localhost:8080/ in your browser
- **Access the console**: Open the console URL with admin/password
- **Run kubectl commands**: In another terminal, use the kubeconfig paths shown
- **Test the application**: Interact with the deployed services
- **Inspect resources**: Check deployments, pods, services, etc.

Example in another terminal:

```bash
# Set kubeconfig for west site
export KUBECONFIG=/tmp/sketcher/config-west

# Check running pods
kubectl get pods

# Check skupper status
skupper status

# View logs
kubectl logs deployment/frontend
```

### 4. Extending the Demo

While the demo is paused, you can extend it with additional steps:

```bash
# In another terminal
./sketcher-go demo-extend examples/skewer-extend-observability.yaml
```

This will:
1. Load the saved demo context
2. Validate the demo is still running
3. Run the extension steps in the same environment
4. Return you to the paused demo state

### 5. Finishing the Demo

When done exploring, type `yes` at the prompt:

```
Are you done (yes)? yes
```

This will:
1. Run the `cleaning_up` step
2. Stop the Minikube tunnel
3. Delete the Minikube cluster
4. Remove temporary files

## Demo Context File

The `.demo-context.json` file stores:

```json
{
  "version": "1.0",
  "created_at": 1234567890,
  "pid": 12345,
  "work_dir": "/tmp/sketcher",
  "yaml_file": "examples/skupper-example-hello-world.yaml",
  "sites": {
    "west": {
      "platform": "kubernetes",
      "namespace": "west",
      "env": {
        "KUBECONFIG": "/tmp/sketcher/config-west"
      },
      "title": "West"
    },
    "east": {
      "platform": "kubernetes",
      "namespace": "east",
      "env": {
        "KUBECONFIG": "/tmp/sketcher/config-east"
      },
      "title": "East"
    }
  },
  "demo_active": true
}
```

This allows `demo-extend` to:
- Restore the exact environment
- Reuse the same kubeconfigs
- Execute new steps in the existing sites

## Environment Variables

### SKETCHER_DEMO

Set automatically by the `demo` command. Tells the executor to:
- Skip the `cleaning_up` step
- Save demo context
- Pause for interaction

### SKETCHER_DEMO_NO_WAIT

Skip the interactive pause (useful for CI/testing):

```bash
SKETCHER_DEMO_NO_WAIT=1 ./sketcher-go demo example.yaml
```

## Implementation Details

### Demo Context Save (`demo.SaveDemoContext`)

Extracts and saves:
- Site configurations (platform, namespace, env, title)
- Work directory path
- YAML file path
- Process ID
- Timestamp

### Demo Pause (`demo.PauseForDemo`)

1. Checks for frontend deployment → shows frontend URL
2. Checks for Skupper console → shows console URL and credentials
3. Displays site environment setup
4. Waits for user input

### Demo Extend (`demo.CreateExtendedModel`)

1. Loads saved context
2. Validates demo is still running (checks PID)
3. Creates synthetic YAML with:
   - Original site configurations
   - Extension steps from extend file
4. Runs steps in existing environment

## Error Handling

### Demo Not Found

```
Error: no active demo found. Run 'sketcher demo' first in another terminal.
```

Solution: Start a demo first with `./sketcher-go demo`

### Demo No Longer Running

```
Error: demo process (PID 12345) is no longer running. Please restart the demo.
```

Solution: The original demo process exited. Start a new demo.

### Kubeconfig Not Found

```
Error: kubeconfig for site 'west' not found: /tmp/sketcher/config-west
```

Solution: The demo was cleaned up. Start a new demo.

## Comparison with Test Mode

| Feature | Demo Mode | Test Mode |
|---------|-----------|-----------|
| Purpose | Interactive exploration | Automated testing |
| Pause | Yes, waits for user | No, runs to completion |
| Cleanup | After user confirmation | Automatic |
| Extensions | Supported | Not supported |
| Use Case | Learning, presentations | CI/CD, validation |

## Use Cases

### 1. Learning Skupper

Demo mode lets you:
- See Skupper in action
- Explore the deployed resources
- Test the connections
- Understand the network topology

### 2. Presentations

Perfect for live demos:
- Run the demo
- Show the application working
- Inspect the infrastructure
- Explain concepts while paused

### 3. Development

Test changes interactively:
- Run main setup
- Pause to verify state
- Add extension steps
- Iterate on configuration

### 4. Troubleshooting

Debug issues:
- Run to a specific point
- Pause to inspect
- Check logs and state
- Extend with diagnostic steps

## Files

- `internal/demo/demo.go` - Core demo functionality
- `internal/executor/executor.go` - Demo mode execution
- `internal/cli/cli.go` - Demo command implementation
- `.demo-context.json` - Saved demo state (in work dir)

## Example Workflow

```bash
# Terminal 1: Start demo
./sketcher-go demo examples/skupper-example-hello-world.yaml

# Output shows:
# Frontend URL: http://localhost:8080/
# Console URL: https://10.96.0.123:8010/
# Are you done (yes)?

# Terminal 2: Explore
export KUBECONFIG=/tmp/sketcher/config-west
kubectl get pods
skupper status

# Browser: Open http://localhost:8080/

# Terminal 2: Extend
./sketcher-go demo-extend examples/skewer-extend-observability.yaml

# Terminal 1: When done
# Type: yes
```

The demo mode is now **fully implemented** and provides the complete interactive experience!
