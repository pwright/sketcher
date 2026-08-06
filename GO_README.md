# Sketcher Go Implementation

This is a Go reimplementation of the Sketcher Python framework for documenting and testing Skupper examples.

## Building

```bash
go build -o sketcher-go ./cmd/sketcher
```

## Usage

The Go version supports the same commands as the Python version:

```bash
./sketcher-go resolve <input.yaml> [-o output.yaml] [--in-place]
./sketcher-go generate [skewer.yaml] [-o README.md]
./sketcher-go run [skewer.yaml] [kubeconfigs...] [--debug] [--verbose] [--quiet] [--work-dir DIR]
./sketcher-go demo [skewer.yaml] [kubeconfigs...] [--kind] [--debug] [--verbose] [--quiet]
./sketcher-go demo-extend <extend-file.yaml> [--debug] [--verbose] [--quiet]
./sketcher-go test [skewer.yaml] [--kind] [--debug] [--verbose] [--quiet]
./sketcher-go clean
```

## Architecture

The Go implementation follows the same modular structure as the Python version:

- `cmd/sketcher/main.go` - Main entry point
- `internal/cli/` - Command-line interface
- `internal/model/` - Core data model (Model, Site, Step, Command)
- `internal/resolver/` - Standard step expansion (migration tool)
- `internal/generator/` - README generation
- `internal/executor/` - Step execution
- `internal/kubernetes/` - Kubernetes operations
- `internal/demo/` - Demo mode functionality
- `internal/minikube/` - Minikube integration
- `internal/kind/` - Kind integration
- `internal/utils/` - Utility functions

## Key Differences from Python Version

1. **Type Safety**: Go's static typing catches errors at compile time
2. **Performance**: Compiled binary is faster than interpreted Python
3. **No External Dependencies**: Only uses Go standard library and yaml.v3
4. **Simplified Deployment**: Single binary with no runtime dependencies
5. **Error Handling**: Explicit error returns instead of exceptions

## Status

This Go implementation provides feature parity with the Python version and includes all core functionality:

- ✅ Resolve command (expand standard steps)
- ✅ Generate command (create README from skewer.yaml)
- ✅ Run command (execute steps)
- ✅ Demo command (interactive demo mode)
- ✅ Demo-extend command (extend running demos)
- ✅ Test command (full test workflow)
- ✅ Clean command (cleanup generated files)
- ✅ Minikube integration
- ✅ Kind integration
- ✅ Kubernetes operations
- ✅ Colored logging output
- ✅ Quiet/verbose modes
- ✅ Debug output on failure

## Testing

You can test the Go version alongside the Python version to verify compatibility:

```bash
# Compare help output
python -m sketcher --help
./sketcher-go --help

# Test resolve command
python -m sketcher resolve tests/fixtures/skewer.yaml -o /tmp/python-resolved.yaml
./sketcher-go resolve tests/fixtures/skewer.yaml -o /tmp/go-resolved.yaml
diff /tmp/python-resolved.yaml /tmp/go-resolved.yaml
```

## Development

To modify the Go version:

1. Edit files in `cmd/` or `internal/`
2. Run `go build -o sketcher-go ./cmd/sketcher`
3. Test with `./sketcher-go <command>`

The Go code follows standard Go conventions and project layout.
