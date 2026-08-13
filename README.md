# Sketcher

[![main](https://github.com/skupperproject/skewer/actions/workflows/main.yaml/badge.svg)](https://github.com/skupperproject/skewer/actions/workflows/main.yaml)

**Automate Skupper example documentation and testing from a single YAML file.**

## What You Can Accomplish

With Sketcher, you can:

- **Generate consistent documentation** - Write steps once in YAML, get formatted README.md with copy-paste commands
- **Test examples automatically** - Run full multi-cluster demos in CI/CD without manual setup  
- **Demo interactively** - Pause before cleanup to explore running applications and Skupper networking
- **Validate before deployment** - Test Skupper configurations locally before pushing to production
- **Work across platforms** - Same YAML runs on Kubernetes, Podman, Docker, and systemd

**Quick start**: Install, create `skewer.yaml`, run `sketcher demo` to see your Skupper example working in under 60 seconds.

---

## How It Works

Sketcher uses two command-line tools:
- **`skewer`** (Python) - Processes YAML and generates documentation
- **`sketcher`** (Go) - Executes steps, provisions clusters, runs tests

Both read the same `skewer.yaml` file describing your Skupper example's sites, steps, and commands.

---

## Contents

- [Sketcher](#sketcher)
  - [What You Can Accomplish](#what-you-can-accomplish)
  - [How It Works](#how-it-works)
  - [Contents](#contents)
  - [Try Sketcher (5-Minute Start)](#try-sketcher-5-minute-start)
  - [Set Up Your Own Example](#set-up-your-own-example)
  - [Write Your skewer.yaml](#write-your-skeweryaml)
    - [Top-Level Structure](#top-level-structure)
  - [Common Patterns](#common-patterns)
  - [Demo and Test Modes](#demo-and-test-modes)
    - [Demo Mode: Interactive Exploration](#demo-mode-interactive-exploration)
    - [Test Mode: Automated Validation](#test-mode-automated-validation)
  - [Extend Running Demos](#extend-running-demos)
    - [Approach 1: Interactive Extensions (`demo-extend`)](#approach-1-interactive-extensions-demo-extend)
    - [Approach 2: Batch Testing (`test` with extensions)](#approach-2-batch-testing-test-with-extensions)
  - [Migration from Skewer](#migration-from-skewer)
  - [Choose Your Cluster Provider](#choose-your-cluster-provider)
  - [Troubleshooting](#troubleshooting)
    - [Viewing Execution Logs](#viewing-execution-logs)
    - [Subnet is already used](#subnet-is-already-used)
    - [Sketcher command not found after installation](#sketcher-command-not-found-after-installation)
    - [Resolver fails on old Skewer YAML](#resolver-fails-on-old-skewer-yaml)
  - [Contributing](#contributing)
  - [License](#license)
  - [About This Documentation](#about-this-documentation)

---

## Try Sketcher (5-Minute Start)

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

**Next**: See [Set Up Your Own Example](#set-up-your-own-example) to create your own Skupper documentation and tests.

---

## Set Up Your Own Example

**Install both tools:**

```bash
# Install skewer (Python - for YAML processing and doc generation)
pip install sketcher

# Install sketcher (Go - for execution)
# Option 1: Use pre-built binaries
cd /path/to/sketcher
sudo cp sketcher-linux-x64 /usr/local/bin/sketcher     # Linux
# or
sudo cp sketcher-mac-arm64 /usr/local/bin/sketcher     # macOS (Apple Silicon)

# Option 2: Build from source
go build -o sketcher cmd/sketcher/main.go
sudo mv sketcher /usr/local/bin/
```

**Development builds:**

```bash
# Build for current platform
just build-go

# Build for all platforms (Linux x64, macOS ARM64)
just build-go-all
```

**Verify installation:**

```bash
skewer --help       # Python tool (resolve, generate, clean)
sketcher --help     # Go tool (run, demo, test, clean)
```

**Create your Skupper example:**

```bash
cd my-skupper-example/
```

Create a `skewer.yaml` file describing your example:

```bash
<editor> skewer.yaml
```

**Generate README and test:**

```bash
# Generate README.md from your skewer.yaml (Python tool)
skewer generate skewer.yaml

# Run the example steps in demo mode (pauses before cleanup) (Go tool)
sketcher demo skewer.yaml

# Run full automated test (no pause) (Go tool)
sketcher test skewer.yaml

# Debugging flags (works with demo, run, test commands)
sketcher demo skewer.yaml --verbose  # Show debug output (what's executing)
sketcher demo skewer.yaml --debug    # Show debug output on failure
sketcher demo skewer.yaml --quiet    # Suppress progress messages

# Cluster provider options
sketcher demo skewer.yaml --kind        # Use Kind with NodePort ingress
sketcher demo skewer.yaml --kind-lb     # Use Kind with MetalLB (LoadBalancer ingress)
sketcher test skewer.yaml --kind        # Use Kind for test runs
sketcher test skewer.yaml --kind-lb     # Use Kind with LoadBalancer for tests

# Note: Ingress type comparison
#   - Minikube (default): LoadBalancer ingress
#   - Kind (--kind): NodePort ingress
#   - Kind (--kind-lb): LoadBalancer ingress via MetalLB
# macOS users: Kind requires Docker Desktop or Colima to be running
#   - Docker Desktop: NodePort works out-of-the-box
#   - Colima: Start with `colima start --network-address` for direct NodePort access
```

**Note:** The `sketcher test` command requires both tools - it calls `skewer generate` to create documentation, then runs the execution steps.

## Write Your skewer.yaml

Define your Skupper example's sites, steps, and commands in YAML format.

### Top-Level Structure

The top level of the `skewer.yaml` file:

```yaml
title:              # Your example's title (required)
subtitle:           # Your chosen subtitle (optional)
workflow:           # The filename of your GitHub workflow (optional, default 'main.yaml')
overview:           # Text introducing your example (optional)
prerequisites:      # Text describing prerequisites (optional, has default text)
sites:              # A map of named sites (see below)
steps:              # A list of steps (see below)
summary:            # Text to summarize what the user did (optional)
next_steps:         # Text linking to more examples (optional, has default text)
```

For fields with default text such as `prerequisites` and `next_steps`, you can include the default text inside your custom text by using the `@default@` placeholder:

```yaml
next_steps:
    @default@

    This Way to the Egress.
```

To disable the GitHub workflow and CI badge, set `workflow` to `null`.

A **site**:

```yaml
<site-name>:
  title:            # The site title (optional)
  platform:         # "kubernetes", "podman", "docker", or "linux" (required)
  namespace:        # The Kubernetes namespace (required for Kubernetes sites)
  env:              # A map of named environment variables
```

Kubernetes sites must have a `KUBECONFIG` environment variable with a path to a kubeconfig file. A tilde (~) in the kubeconfig file path is replaced with a temporary working directory during testing.

Podman, Docker, and Linux sites must have a `SKUPPER_PLATFORM` variable with the appropriate value (`podman`, `docker`, or `linux`).

Example sites:

```yaml
sites:
  west:
    title: West
    platform: kubernetes
    namespace: west
    env:
      KUBECONFIG: ~/.kube/config-west
  east:
    title: East
    platform: podman
    env:
      SKUPPER_PLATFORM: podman
  north:
    title: North
    platform: docker
    env:
      SKUPPER_PLATFORM: docker
```

A **step**:

```yaml
- title:            # The step title (required)
  preamble:         # Text before the commands (optional)
  commands:         # Named groups of commands. See below.
  postamble:        # Text after the commands (optional)
```

An example step:

```yaml
steps:
  - title: Expose the frontend service
    preamble: |
      We have established connectivity between the two namespaces and
      made the backend in `east` available to the frontend in `west`.
      Before we can test the application, we need external access to
      the frontend.

      Use `kubectl expose` with `--type LoadBalancer` to open network
      access to the frontend service.
    commands:
      west:
        - run: kubectl expose deployment/frontend --port 8080 --type LoadBalancer
        - await_ingress: service/frontend
        - run: kubectl get service/frontend
          output: |
            NAME       TYPE           CLUSTER-IP      EXTERNAL-IP      PORT(S)          AGE
            frontend   LoadBalancer   10.103.232.28   10.103.232.28    8080:30407/TCP   15s
```

The step commands are separated into named groups corresponding to the sites. Each named group contains a list of command entries.

A **command**:

```yaml
- run:              # A shell command (required)
  apply:            # Use this command only for "readme" or "test" (default is both)
  output:           # Sample output to include in the README (optional)
  expect_failure:   # If true, check that the command fails and keep going (default false)
```

Only the `run` and `output` fields appear in the generated README. The `output` field is used as sample output only, not for any kind of testing.

**The `apply` field** is useful when you want the README instructions to be different from the test procedure:

```yaml
commands:
  west:
    - run: export KUBECONFIG=~/.kube/config-west
      apply: readme    # Only appears in generated README
    
    - run: kubectl create namespace west --dry-run=client -o yaml | kubectl apply -f -
      apply: test      # Only runs during test/demo execution
    
    - run: kubectl config set-context --current --namespace west
      # No apply field = runs everywhere (README + test/demo)
```

**apply values:**
- `readme` - Command only appears in the generated README, skipped during execution
- `test` - Command only runs during test/demo/run modes, omitted from README
- No `apply` field - Command appears in README AND runs during execution

There are also special "await" commands that pause execution until a condition is met. They are used only for testing and do not impact the README:

```yaml
- await_resource:     # Wait for a resource to be ready
                      # Example: await_resource: deployment/frontend

- await_ingress:      # Wait for a service to have an external hostname or IP
                      # Example: await_ingress: service/frontend

- await_http_ok:      # Wait for an HTTP endpoint to return 200 OK
                      # Example: await_http_ok: [service/frontend, "http://{}:8080/api/health"]

- await_port:         # Wait for a TCP port to be available
                      # Example: await_port: 8080

- await_console_ok:   # Wait for Skupper console to be ready
                      # Example: await_console_ok: true
```

Example commands with await operations:

```yaml
commands:
  east:
    - run: skupper expose deployment/backend --port 8080
      output: |
        deployment backend exposed as backend
  west:
    - await_resource: service/backend
    - run: kubectl get service/backend
      output: |
        NAME      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
        backend   ClusterIP   10.102.112.121   <none>        8080/TCP   30s
```

## Common Patterns

Use these step patterns as templates for your Skupper examples. Sketcher uses explicit YAML rather than hidden templates, making behavior clearer and easier to debug.

**Access your Kubernetes clusters:**

```yaml
- title: Configure separate console sessions
  preamble: |
    Skupper is designed for multicluster application deployments.
    To enable this, you need to run commands in separate
    Kubernetes namespaces. For convenience, you can also set the
    `KUBECONFIG` environment variable for each console session.
  commands:
    west:
      - run: export KUBECONFIG=~/.kube/config-west
        apply: readme
    east:
      - run: export KUBECONFIG=~/.kube/config-east
        apply: readme
  postamble: |
    Each of these `export` commands sets the `KUBECONFIG`
    environment variable to a custom path. You can use
    any path you choose.
```

**Create your namespaces:**

```yaml
- title: Create your namespaces
  preamble: |
    Use `kubectl create namespace` to create the namespaces you
    wish to use.
  commands:
    west:
      - run: kubectl create namespace west
      - run: kubectl config set-context --current --namespace west
    east:
      - run: kubectl create namespace east
      - run: kubectl config set-context --current --namespace east
```

**Create your Skupper sites:**

```yaml
- title: Create your sites
  preamble: |
    A Skupper site is a location where components of your
    application are running. Sites are linked together to form a
    Skupper network for your application.

    For this example, you need two Skupper sites, one in each
    namespace.
  commands:
    west:
      - run: skupper init --site-name west
        output: |
          Skupper is now installed in namespace 'west'.  Use 'skupper
          status' to get more information.
    east:
      - run: skupper init --site-name east
        output: |
          Skupper is now installed in namespace 'east'.  Use 'skupper
          status' to get more information.
```

**Link your sites:**

```yaml
- title: Link your sites
  preamble: |
    A Skupper link is a channel for communication between two
    sites. Links serve as a transport for application connections
    and requests.
  commands:
    west:
      - await_resource: deployment/skupper-router
      - run: skupper token create ~/west.token
        output: |
          Token written to ~/west.token
    east:
      - await_resource: deployment/skupper-router
      - run: skupper link create ~/west.token
        output: |
          Site configured to link to west:8081 (name=link1)
          Check the status of the link using 'skupper link status'.
      - run: skupper link status --wait 60
```

**Cleaning up:**

```yaml
- title: Cleaning up
  preamble: |
    To remove Skupper and the other resources from this exercise,
    use the following commands.
  commands:
    west:
      - run: skupper delete
      - run: kubectl delete service/frontend
      - run: kubectl delete deployment/frontend
    east:
      - run: skupper delete
      - run: kubectl delete deployment/backend
```

For more complete examples, see the [sketcher_yamls](../sketcher_yamls/) directory.

## Demo and Test Modes

Sketcher provides two execution modes depending on whether you need interactive exploration or automated validation.

### Demo Mode: Interactive Exploration

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

### Test Mode: Automated Validation

Test mode runs all steps automatically, generates documentation, validates output, then cleans up. Perfect for CI/CD pipelines.

```bash
# Run full automated test (no pause, auto-cleanup)
sketcher test skewer.yaml

# With cluster provider options
sketcher test --kind-lb skewer.yaml  # Fast CI/CD testing
```

---

## Extend Running Demos

Add observability, scaling, or chaos testing to a running demo without restarting clusters. Sketcher provides two complementary approaches:

### Approach 1: Interactive Extensions (`demo-extend`)

Attach to a running demo and execute additional scenarios while keeping clusters and services active. Perfect for iterative testing, adding observability, or exploring different configurations.

**Usage:**

In one terminal, start the demo:

```console
$ sketcher demo skewer.yaml
```

The demo will execute all setup steps and then pause, displaying connection information.

In a separate terminal, run additional test scenarios:

```console
$ sketcher demo-extend skewer-extend-observability.yaml
$ sketcher demo-extend skewer-extend-scaling.yaml
$ sketcher demo-extend skewer-extend-chaos.yaml
```

Each `demo-extend` invocation:
- Attaches to the running demo's environment (same kubeconfigs, namespaces, clusters)
- Executes the steps defined in the extension YAML file
- Exits while leaving the demo running for further testing

The extension YAML files follow the same format as `skewer.yaml` but only require a `steps` section (sites are inherited from the running demo):

```yaml
# skewer-extend-observability.yaml
title: Add Skupper Network Observer
steps:
  - title: Install Skupper Network Observer
    preamble: |
      The Network Observer provides a web console for monitoring
      your Skupper network in real time.
    commands:
      west:
        - run: helm install skupper-network-observer oci://quay.io/skupper/helm/network-observer --version 2.2.1
        - run: kubectl create route passthrough skupper-console --service=skupper-network-observer --port=https
        - run: kubectl get secret skupper-network-observer-auth -o jsonpath='{.data.htpasswd}' | base64 -d
          output: |
            admin:password123
```

**Common use cases for demo extensions:**
- Adding observability tools (Network Observer, Prometheus)
- Testing scaling scenarios
- Demonstrating optional features
- Chaos/failure testing
- Performance testing variations

When finished, return to the first terminal and type `yes` to clean up and exit.

### Approach 2: Batch Testing (`test` with extensions)

The `test` command automatically discovers and runs all test scenarios in a single batch execution. Ideal for CI/CD pipelines.

**Usage:**

```console
$ sketcher test skewer.yaml
```

This command:
1. Generates the README (verifies documentation is up to date)
2. Discovers all `skewer-extend-*.yaml` files in the current directory
3. Concatenates their steps to the base `skewer.yaml` steps
4. Runs all steps in sequence on Minikube
5. Cleans up automatically when complete

If no `skewer-extend-*.yaml` files exist, `test` runs only the base `skewer.yaml` (backward compatible).

**Example project structure:**

```
my-skupper-example/
  skewer.yaml                      # Base: setup, deploy app, basic smoke test
  skewer-extend-observability.yaml # Add Network Observer
  skewer-extend-scaling.yaml       # Test scaling scenarios
  skewer-extend-failure.yaml       # Chaos/failure testing
  README.md                        # Generated documentation
```

**GitHub Actions example:**

```yaml
name: Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Sketcher
        run: |
          pip install pyyaml
          pip install -e /path/to/sketcher
      - name: Run all tests
        run: sketcher test skewer.yaml
```

The `test` command runs all extension files automatically, in alphabetical order.

**When to use each approach:**

- Use `demo` + `demo-extend` for interactive development and debugging
- Use `test` for automated CI/CD pipelines and comprehensive test runs

## Migration from Skewer

If you have existing Skewer YAML files that use `standard:` step references, use the `skewer resolve` command to expand them into explicit YAML:

```bash
# Expand standard steps
skewer resolve old-skewer.yaml -o new-skewer.yaml

# Or modify in-place
skewer resolve skewer.yaml --in-place

# Batch process multiple files
for f in examples/*/skewer.yaml; do
  skewer resolve "$f" --in-place
done
```

**Why explicit YAML?**

Sketcher uses fully expanded YAML instead of runtime step expansion because:
- **Clearer behavior** - No hidden magic, what you see is what runs
- **Easier debugging** - All commands visible in the YAML file
- **Better git diffs** - Changes are explicit in version control
- **Simpler code** - No complex runtime expansion logic

**Batch migration results:**
- ✅ 19/30 real Skupper examples resolved (63%)
- ✅ 100% success rate on modern examples (2024+)
- ⚠️ Failures only on very old yamls with unprefixed step names

For new examples, use the common step patterns shown above rather than relying on a standard steps library.

---

## Choose Your Cluster Provider

By default, Sketcher starts a local Minikube instance automatically. Choose a different provider based on your performance needs and environment.

**Cluster provider comparison:**
- **Minikube** (default) - Uses LoadBalancer ingress, slower startup, higher resource usage
- **Kind** (`--kind` flag) - Uses NodePort ingress, faster startup, lower resource usage, better for CI/CD
  - **macOS prerequisite**: Requires Docker Desktop or Colima to be running for port forwarding
    - Docker Desktop: Works out-of-the-box
    - Colima: Start with `colima start --network-address` for direct NodePort access
- **Kind with MetalLB** (`--kind-lb` flag) - Uses LoadBalancer ingress like Minikube, but with Kind's speed
  - Automatically installs and configures MetalLB
  - No need for `--ingress nodeport` in Skupper commands (uses standard LoadBalancer)
  - Best of both: Kind's speed + LoadBalancer ingress compatibility

**Configuring Skupper for different cluster providers:**

The Skupper configuration depends on which cluster provider and ingress type you're using:

```yaml
# Minikube (default) - LoadBalancer ingress:
- run: skupper site create west --enable-link-access

# Kind with --kind-lb flag - LoadBalancer via MetalLB (same as Minikube):
- run: skupper site create west --enable-link-access

# Kind with --kind flag - NodePort ingress:
- run: skupper site create west --ingress nodeport --ingress-host localhost --enable-link-access
```

**When to use `--ingress nodeport`:**
- Only needed with `--kind` flag (NodePort mode)
- NOT needed with `--kind-lb` flag (MetalLB provides LoadBalancer)
- NOT needed with default Minikube

**Example for Kind with NodePort (`--kind`):**

```yaml
commands:
  west:
    - run: skupper site create west --ingress nodeport --ingress-host localhost --enable-link-access
  east:
    - run: skupper site create east --ingress nodeport --ingress-host localhost
```

**Note:** This project uses Skupper v2 syntax. The old `skupper init` command from v1 is deprecated and no longer works. Always use `skupper site create`.

Kubeconfigs are assigned to Kubernetes sites **in the order the sites are defined** in `skewer.yaml`. For example, given this site definition:

```yaml
sites:
  west:
    platform: kubernetes
    namespace: west
    env:
      KUBECONFIG: ~/.kube/config-west
  east:
    platform: kubernetes
    namespace: east
    env:
      KUBECONFIG: ~/.kube/config-east
```

`west` is the first Kubernetes site and `east` is the second. To run with a remote OpenShift cluster for `west` and a local Minikube instance for `east`, first start Minikube and export its kubeconfig:

```bash
minikube start -p east
minikube -p east kubeconfig > ~/.kube/config-east-minikube
```

Then pass the kubeconfigs in site order (west first, east second):

```bash
sketcher demo skewer.yaml ~/.kube/config-west-openshift ~/.kube/config-east-minikube
```

Or equivalently for `run`:

```bash
sketcher run skewer.yaml ~/.kube/config-west-openshift ~/.kube/config-east-minikube
```

The provided kubeconfigs override the paths in `skewer.yaml` at runtime — the `skewer.yaml` file itself is not modified. Each kubeconfig must already be authenticated and have the correct namespace context set before running.

## Troubleshooting

### Viewing Execution Logs

Every `sketcher demo`, `test`, and `run` execution automatically generates a detailed log file in `/tmp/sk-logs/`. The log path is printed at the end of each run:

```
Log file: /tmp/sk-logs/sketcher-demo-20260812-143022.log
```

View logs in human-readable format:

```bash
sketcher view-log /tmp/sk-logs/sketcher-demo-20260812-143022.log
```

The log includes every step, command, wait operation, and error with timestamps and context. Logs persist across runs and are not deleted during cleanup. See [docs/logging.md](docs/logging.md) for details on log format and debugging workflows.

### Subnet is already used

Error:

```console
plano: notice: Starting Minikube
plano: notice: Running command 'minikube start -p skewer --auto-update-drivers false'
* Creating podman container (CPUs=2, Memory=16000MB) ...- E0229 05:44:29.821273   12224 network_create.go:113] error while trying to create podman network skewer 192.168.49.0/24

Error: subnet 192.168.49.0/24 is already used on the host or by another config
```

Remove the existing Podman network. Note that it might belong to another user on the host.

```shell
sudo podman network rm minikube
```

### Sketcher command not found after installation

If `python -m sketcher` fails with "No module named sketcher", ensure you installed Sketcher correctly:

```bash
cd /path/to/sketcher
pip install sketcher
skewer --help && sketcher --help
```

### Resolver fails on old Skewer YAML

Very old Skewer YAML files (pre-2024) may use unprefixed step names. The resolver only recognizes prefixed names like `platform/access_your_kubernetes_clusters`. You'll need to manually update these YAMLs or write explicit steps.

## Contributing

Sketcher is production-ready with 63 passing tests, comprehensive documentation, and validation against 30 real Skupper examples.

For development setup, architecture details, test coverage, and contribution guidelines, see [DEVELOPERS.md](DEVELOPERS.md).

**Quick contributor setup:**

```bash
# Clone and setup
git clone https://github.com/skupperproject/sketcher
cd sketcher
uv venv
source .venv/bin/activate
uv pip install pyyaml pytest

# Run tests
python -m pytest tests/ -v

# Should see: ====== 63 passed ======
```

## License

Same as Skupper project (Apache License 2.0).

---

## About This Documentation

This README is organized using the **Seven-Action Documentation Model** to help you find what you need based on your immediate goal:

| Section | Primary Action | What You Accomplish |
|---------|----------------|---------------------|
| What You Can Accomplish | **Appraise** | Assess whether Sketcher fits your Skupper documentation and testing needs |
| Try Sketcher (5-Minute Start) | **Explore** | Try Sketcher with minimal commitment to see if it works for you |
| Set Up Your Own Example | **Develop** | Create and test your own Skupper example from scratch |
| Write Your skewer.yaml | **Remember** | Look up YAML field syntax, structure, and patterns |
| Common Patterns | **Practice** | Copy and adapt proven step patterns for common Skupper scenarios |
| Demo and Test Modes | **Practice** | Run interactive demos or automated tests depending on your workflow |
| Extend Running Demos | **Develop** | Add observability, scaling, or chaos testing to existing demos |
| Choose Your Cluster Provider | **Appraise** | Select the right cluster provider for your environment and performance requirements |
| Troubleshooting | **Troubleshoot** | Diagnose and resolve installation, networking, and validation errors |

For detailed platform-specific workflows and decision trees, see **[docs/use-cases.md](docs/use-cases.md)**.

---

**Sketcher: Modern Python 3 framework for Skupper examples** 🚀
