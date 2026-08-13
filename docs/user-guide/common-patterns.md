# Common Patterns

Use these step patterns as templates for your Skupper examples. Sketcher uses explicit YAML rather than hidden templates, making behavior clearer and easier to debug.

## Access Your Kubernetes Clusters

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

## Create Your Namespaces

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

## Create Your Skupper Sites

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
      - run: skupper site create west --enable-link-access
        output: |
          Skupper is now installed in namespace 'west'.  Use 'skupper
          status' to get more information.
    east:
      - run: skupper site create east
        output: |
          Skupper is now installed in namespace 'east'.  Use 'skupper
          status' to get more information.
```

!!! note
    This project uses Skupper v2 syntax. The old `skupper init` command from v1 is deprecated.

## Link Your Sites

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

## Cleaning Up

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

## Next Steps

For more complete examples, see the sketcher_yamls directory in the repository.

- [Writing skewer.yaml](writing-skewer-yaml.md) - Full YAML specification
- [Demo and Test Modes](demo-test-modes.md) - Execution options
- [Use Cases](use-cases.md) - Platform-specific workflows
