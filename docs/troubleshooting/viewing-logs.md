# Viewing Execution Logs

Every `sketcher demo`, `test`, and `run` execution automatically generates a detailed log file in `/tmp/sk-logs/`. The log path is printed at the end of each run.

## Log Location

```
Log file: /tmp/sk-logs/sketcher-demo-20260812-143022.log
```

Logs are stored in:

- **Directory**: `/tmp/sk-logs/`
- **Format**: `sketcher-{mode}-{date}-{time}.log`
- **Persistence**: Logs persist across runs and are not deleted during cleanup

## Viewing Logs

View logs in human-readable format:

```bash
sketcher view-log /tmp/sk-logs/sketcher-demo-20260812-143022.log
```

## What's in the Logs

The log includes:

- Every step executed
- Each command run
- Wait operations and their status
- Errors with full context
- Timestamps for all operations
- Environment variables and configuration
- Cluster creation and cleanup details

## Using Logs for Debugging

### Finding Failed Commands

Search for errors:

```bash
grep -i error /tmp/sk-logs/sketcher-demo-*.log
```

### Checking Specific Steps

Find a specific step:

```bash
grep "Step:" /tmp/sk-logs/sketcher-demo-*.log
```

### Viewing Recent Logs

List recent log files:

```bash
ls -lht /tmp/sk-logs/ | head -10
```

View the most recent log:

```bash
sketcher view-log $(ls -t /tmp/sk-logs/sketcher-*.log | head -1)
```

## Log Format Details

For detailed information about log format, structured logging, and debugging workflows, see:

- [Logging Overview](../configuration/logging.md)
- [Logging Example](../configuration/logging-example.md)
- [Logging Reference](../configuration/logging-reference.md)
- [Logging Implementation](../development/logging-implementation.md)

## Next Steps

- See [Common Issues](common-issues.md) for specific error solutions
- Learn about [Configuration](../configuration/logging.md) for log customization
