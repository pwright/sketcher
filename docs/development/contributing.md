# Contributing to Sketcher

Thank you for your interest in contributing to Sketcher! This guide will help you get started.

## Development Setup

See the [Developer Guide](developer-guide.md) for detailed setup instructions including:

- Installing dependencies
- Building from source
- Running tests
- Development workflows

## Project Structure

Sketcher is a dual-language project:

- **`sketcher/`** (Python) - YAML processing and documentation generation
- **`cmd/sketcher/`** (Go) - Execution engine for demos and tests

## Making Changes

### 1. Fork and Clone

```bash
git clone https://github.com/your-username/sketcher.git
cd sketcher
```

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Your Changes

- Write clear, concise commit messages
- Add tests for new functionality
- Update documentation as needed
- Run tests locally before pushing

### 4. Test Your Changes

```bash
# Python tests
pytest

# Go tests
go test ./...

# Build both tools
just build-go
pip install -e .

# Test end-to-end
sketcher demo examples/hello-world/skewer.yaml
```

### 5. Submit a Pull Request

- Push your branch to your fork
- Create a pull request against the main branch
- Describe your changes clearly
- Link any related issues

## Code Style

### Python

- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small

### Go

- Run `gofmt` before committing
- Follow standard Go conventions
- Use meaningful names
- Add comments for exported functions

## Testing

### Python Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=sketcher
```

### Go Tests

```bash
# Run all tests
go test ./...

# Run with verbose output
go test -v ./...
```

## Documentation

### Updating Documentation

- Documentation lives in `docs/`
- Use Markdown format
- Test locally with `mkdocs serve`
- Update navigation in `mkdocs.yml` if adding new pages

### Schema Documentation

When changing the skewer.yaml schema:

1. Update [Schema Documentation](schema.md)
2. Update [JSON Schema files](../configuration/json-schema-quickstart.md)
3. Add examples to [Writing skewer.yaml](../user-guide/writing-skewer-yaml.md)

## Reporting Issues

- Use GitHub Issues
- Provide a clear description
- Include steps to reproduce
- Share error messages and logs
- Specify your environment (OS, Python/Go versions)

## Questions?

- Check the [Developer Guide](developer-guide.md)
- Look at existing pull requests
- Open a GitHub Discussion
- Review [Use Cases](../user-guide/use-cases.md) for examples

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
