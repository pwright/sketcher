# Logging Example

This example shows what a typical log file looks like and how to use it for debugging.

## Example Run

Given this simple `skewer.yaml`:

```yaml
title: Hello World Example
sites:
  public:
    platform: kubernetes
    namespace: public
    kubeconfig: ~/.kube/config
steps:
  - title: Deploy application
    commands:
      public:
        - run: kubectl create deployment hello --image=nginx
        - await_resource: deployment/hello
  - title: Expose service
    commands:
      public:
        - run: kubectl expose deployment hello --port=80
        - run: curl http://hello
```

## Generated Log

Running `sketcher demo skewer.yaml` generates a log like this:

```json
{"timestamp":"2026-08-12T14:30:22Z","type":"info","message":"Run started","context":{"run_type":"demo","yaml_file":"skewer.yaml","work_dir":"/tmp/sketcher-xyz123"}}
{"timestamp":"2026-08-12T14:30:23Z","type":"step","step_number":1,"step_name":"Deploy application"}
{"timestamp":"2026-08-12T14:30:24Z","type":"command","site":"public","command":"kubectl create deployment hello --image=nginx","context":{"background":false}}
{"timestamp":"2026-08-12T14:30:25Z","type":"wait","wait_type":"resource","wait_target":"deployment/hello","wait_timeout":300,"site":"public"}
{"timestamp":"2026-08-12T14:30:30Z","type":"step_complete","step_number":1,"step_name":"Deploy application","duration":7.234}
{"timestamp":"2026-08-12T14:30:31Z","type":"step","step_number":2,"step_name":"Expose service"}
{"timestamp":"2026-08-12T14:30:32Z","type":"command","site":"public","command":"kubectl expose deployment hello --port=80","context":{"background":false}}
{"timestamp":"2026-08-12T14:30:33Z","type":"command","site":"public","command":"curl http://hello","context":{"background":false}}
{"timestamp":"2026-08-12T14:30:34Z","type":"step_complete","step_number":2,"step_name":"Expose service","duration":3.156}
{"timestamp":"2026-08-12T14:30:35Z","type":"info","message":"Run completed","context":{"total_duration_seconds":13.5,"total_steps":2}}
```

## Viewing the Log

```bash
$ sketcher view-log /tmp/sketcher-xyz123/sketcher-demo-20260812-143022.log

[14:30:22] INFO: Run started
  run_type: demo
  yaml_file: skewer.yaml
  work_dir: /tmp/sketcher-xyz123

[14:30:23] STEP 1: Deploy application
──────────────────────────────────

[14:30:24] CMD [public]: kubectl create deployment hello --image=nginx
[14:30:25] WAIT [public]: resource for deployment/hello (timeout: 300s)
[14:30:30] ✓ Step 1 completed in 7.23s

[14:30:31] STEP 2: Expose service
─────────────────────────────

[14:30:32] CMD [public]: kubectl expose deployment hello --port=80
[14:30:33] CMD [public]: curl http://hello
[14:30:34] ✓ Step 2 completed in 3.16s

[14:30:35] INFO: Run completed
  total_duration_seconds: 13.5
  total_steps: 2
```

## Debugging Example

If the curl command failed, the log would show:

```json
{"timestamp":"2026-08-12T14:30:33Z","type":"command","site":"public","command":"curl http://hello","context":{"background":false}}
{"timestamp":"2026-08-12T14:30:34Z","type":"error","error":"command failed in step 2 'Expose service': exit status 7","context":{"step":"step 2 'Expose service'"}}
```

Viewing with `sketcher view-log`:

```
[14:30:33] CMD [public]: curl http://hello
[14:30:34] ERROR: command failed in step 2 'Expose service': exit status 7
  step: step 2 'Expose service'
```

You can then:
1. See the exact command that failed
2. Check what ran before it
3. Reproduce the issue manually with the same command
4. Fix the YAML and retry

## Querying Logs with jq

Extract all commands:
```bash
$ jq -r 'select(.type == "command") | .command' sketcher-demo-20260812-143022.log
kubectl create deployment hello --image=nginx
kubectl expose deployment hello --port=80
curl http://hello
```

Find long-running steps:
```bash
$ jq -r 'select(.type == "step_complete" and .duration > 5) | "\(.step_name): \(.duration)s"' sketcher-demo-20260812-143022.log
Deploy application: 7.234s
```

Check for waits:
```bash
$ jq 'select(.type == "wait")' sketcher-demo-20260812-143022.log
{
  "timestamp": "2026-08-12T14:30:25Z",
  "type": "wait",
  "wait_type": "resource",
  "wait_target": "deployment/hello",
  "wait_timeout": 300,
  "site": "public"
}
```

## Background Commands

Background commands (ending with `&`) are logged with context:

```json
{"timestamp":"2026-08-12T14:30:40Z","type":"command","site":"public","command":"python -m http.server 8080","context":{"background":true}}
```

Viewing:
```
[14:30:40] CMD [public] (background): python -m http.server 8080
```

## Multi-Site Logging

For examples with multiple sites, logs show which site executed each command:

```
[14:30:24] CMD [west]: skupper site create west
[14:30:30] CMD [east]: skupper site create east
[14:30:35] WAIT [west]: resource for deployment/skupper-router (timeout: 300s)
[14:30:36] WAIT [east]: resource for deployment/skupper-router (timeout: 300s)
```

This makes it easy to trace issues specific to one site.
