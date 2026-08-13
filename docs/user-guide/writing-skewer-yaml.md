# Writing skewer.yaml

Define your Skupper example's sites, steps, and commands in YAML format.

## Top-Level Structure

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

## Sites

A **site** represents a location where components of your application are running:

```yaml
<site-name>:
  title:            # The site title (optional)
  platform:         # "kubernetes", "podman", "docker", or "linux" (required)
  namespace:        # The Kubernetes namespace (required for Kubernetes sites)
  env:              # A map of named environment variables
```

Kubernetes sites must have a `KUBECONFIG` environment variable with a path to a kubeconfig file. A tilde (~) in the kubeconfig file path is replaced with a temporary working directory during testing.

Podman, Docker, and Linux sites must have a `SKUPPER_PLATFORM` variable with the appropriate value (`podman`, `docker`, or `linux`).

### Example Sites

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

## Steps

A **step** represents a phase in your example workflow:

```yaml
- title:            # The step title (required)
  preamble:         # Text before the commands (optional)
  commands:         # Named groups of commands. See below.
  postamble:        # Text after the commands (optional)
```

### Example Step

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

## Commands

A **command** represents an action to execute:

```yaml
- run:              # A shell command (required)
  apply:            # Use this command only for "readme" or "test" (default is both)
  output:           # Sample output to include in the README (optional)
  expect_failure:   # If true, check that the command fails and keep going (default false)
```

Only the `run` and `output` fields appear in the generated README. The `output` field is used as sample output only, not for any kind of testing.

### The `apply` Field

The `apply` field is useful when you want the README instructions to be different from the test procedure:

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

### Await Commands

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

### Example with Await Operations

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

## Next Steps

- See [Common Patterns](common-patterns.md) for typical step templates
- Learn about [Demo and Test Modes](demo-test-modes.md) for execution options
- Explore [Use Cases](use-cases.md) for platform-specific workflows
