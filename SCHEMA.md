# JSON Schema for skewer.yaml

This document describes the JSON Schema validation for Sketcher's `skewer.yaml` configuration files.

## Files

- **`skewer-schema.json`** - JSON Schema (draft-07) defining the structure of `skewer.yaml` files
- **`scripts/validate-schema.py`** - Python validator (recommended)
- **`scripts/validate-schema.go`** - Go validator (requires dependencies)
- **`scripts/validate-schema.sh`** - Shell script for basic validation

## Quick Start

### Python Validation (Recommended)

```bash
# Install dependencies
pip install jsonschema

# Validate single file
python scripts/validate-schema.py skewer.yaml

# Validate multiple files
python scripts/validate-schema.py examples/*.yaml

# Example output:
# examples/skewer-extend-observability.yaml  ✓ Valid
# tests/fixtures/skewer-resolved.yaml        ✓ Valid
# 
# ✓ All 2 file(s) valid
```

### Go Validation

```bash
# Install dependencies
go get github.com/xeipuuv/gojsonschema
go get gopkg.in/yaml.v3

# Build validator
go build -o validate-schema scripts/validate-schema.go

# Run validation
./validate-schema skewer.yaml
./validate-schema examples/*.yaml
```

### Shell Script (Basic Validation)

```bash
# Requires: yq, jq (for basic checks only)
./scripts/validate-schema.sh skewer.yaml

# Note: This only checks YAML syntax and required fields
# For full schema validation, use the Python or Go validator
```

## Important: Resolved vs Unresolved YAML

The JSON Schema validates **resolved** `skewer.yaml` files only.

**Unresolved files** contain `standard:` references:
```yaml
steps:
  - standard: platform/access_your_kubernetes_clusters  # ❌ Won't validate
  - standard: skupper/create_your_sites/kubernetes_cli  # ❌ Won't validate
```

**Resolved files** have expanded steps:
```yaml
steps:
  - title: Configure separate console sessions  # ✅ Validates
    commands:
      west:
        - run: export KUBECONFIG=~/.kube/config-west
```

To validate unresolved files, first expand them:
```bash
# Resolve the file
python -m sketcher resolve skewer.yaml -o skewer-resolved.yaml

# Then validate
python scripts/validate-schema.py skewer-resolved.yaml
```

## Schema Features

The JSON Schema validates:

### Required Fields
- ✅ `title` - Example title (string, min 1 char)
- ✅ `sites` - Map of deployment sites (min 1 site)
- ✅ `steps` - List of workflow steps (min 1 step)

### Optional Fields
- `subtitle` - Example subtitle
- `workflow` - GitHub workflow filename (default: `"main.yaml"`, or `null` to disable)
- `overview` - Introduction text (supports `@default@` placeholder)
- `prerequisites` - Prerequisites text (supports `@default@`)
- `summary` - Summary text (supports `@default@`)
- `next_steps` - Next steps text (supports `@default@`)
- `about_this_example` - Additional information

### Site Validation

Each site must have:
- ✅ `platform` - One of: `kubernetes`, `podman`, `docker`, `linux`

**Kubernetes sites** must have:
- ✅ `namespace` - Kubernetes namespace (DNS-1123 format: lowercase, alphanumeric, hyphens)
- ✅ `env.KUBECONFIG` - Path to kubeconfig file

**Podman/Docker/Linux sites** must have:
- ✅ `env.SKUPPER_PLATFORM` - One of: `podman`, `docker`, `linux`

Optional site fields:
- `title` - Display name (defaults to capitalized site name)

### Step Validation

Each step must have:
- ✅ `title` - Step title (string, min 1 char)

Optional step fields:
- `numbered` - Whether to number the step (boolean, default: `true`)
- `name` - Internal name for the step
- `preamble` - Text before commands (supports `@default@`)
- `commands` - Map of site name → command list
- `postamble` - Text after commands (supports `@default@`)

### Command Validation

Commands must have at least one of:
- `run` - Shell command to execute
- `await_resource` - Kubernetes resource to wait for (format: `type/name`)
- `await_ingress` - Service to wait for external IP (format: `service/name`)
- `await_http_ok` - HTTP endpoint to wait for 200 OK (array: `[resource, url_template]`)
- `await_console_ok` - Wait for Skupper console (boolean)
- `await_port` - TCP port to wait for (integer: 1-65535)

Optional command fields:
- `expect_failure` - Expect command to fail (boolean, default: `false`)
- `apply` - When to apply: `readme` or `test`
- `output` - Sample output for README (string)

### Additional Validation

- ❌ **No unknown fields** - Schema rejects unrecognized properties
- ✅ **Conditional validation** - If `platform=kubernetes`, then `namespace` is required
- ✅ **Enum validation** - Platform, apply, SKUPPER_PLATFORM values are restricted
- ✅ **Pattern validation** - Namespace follows Kubernetes DNS-1123 rules
- ✅ **Range validation** - Port numbers must be 1-65535

## IDE Integration

### VS Code

Add to `.vscode/settings.json`:
```json
{
  "yaml.schemas": {
    "./skewer-schema.json": [
      "**/skewer.yaml",
      "**/skewer-*.yaml"
    ]
  }
}
```

### JetBrains IDEs (IntelliJ, PyCharm, GoLand)

1. Open **Settings** → **Languages & Frameworks** → **Schemas and DTDs** → **JSON Schema Mappings**
2. Click **+** to add a new schema
3. **Name**: Skewer YAML
4. **Schema file**: `skewer-schema.json`
5. **Schema version**: JSON Schema version 7
6. Add file patterns: `**/skewer.yaml`, `**/skewer-*.yaml`

### Neovim/Vim with yaml-language-server

Add to your LSP config:
```lua
require'lspconfig'.yamlls.setup {
  settings = {
    yaml = {
      schemas = {
        ["./skewer-schema.json"] = "**/skewer*.yaml"
      }
    }
  }
}
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Validate Schema
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install pyyaml jsonschema
      
      - name: Validate skewer.yaml
        run: python scripts/validate-schema.py skewer.yaml
      
      - name: Validate all examples
        run: python scripts/validate-schema.py examples/skewer-*.yaml
```

### GitLab CI

```yaml
validate-schema:
  image: python:3.11
  script:
    - pip install pyyaml jsonschema
    - python scripts/validate-schema.py skewer.yaml
    - python scripts/validate-schema.py examples/skewer-*.yaml
```

### Pre-commit Hook

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Validate skewer.yaml before committing

if [ -f "skewer.yaml" ]; then
    python scripts/validate-schema.py skewer.yaml || {
        echo "❌ skewer.yaml validation failed"
        exit 1
    }
fi

if [ -f "skewer-resolved.yaml" ]; then
    python scripts/validate-schema.py skewer-resolved.yaml || {
        echo "❌ skewer-resolved.yaml validation failed"
        exit 1
    }
fi
```

## Validation Error Examples

### Missing Required Field

```bash
$ python scripts/validate-schema.py bad.yaml
bad.yaml  ✗ Validation error at root: 'title' is a required property
```

### Invalid Platform Value

```bash
$ python scripts/validate-schema.py bad.yaml
bad.yaml  ✗ Validation error at sites → west → platform: 'k8s' is not one of ['kubernetes', 'podman', 'docker', 'linux']
```

### Missing Namespace for Kubernetes

```bash
$ python scripts/validate-schema.py bad.yaml
bad.yaml  ✗ Validation error at sites → west: 'namespace' is a required property
```

### Invalid Apply Value

```bash
$ python scripts/validate-schema.py bad.yaml
bad.yaml  ✗ Validation error at steps → 0 → commands → west → 0 → apply: 'both' is not one of ['readme', 'test']
```

### Unknown Field

```bash
$ python scripts/validate-schema.py bad.yaml
bad.yaml  ✗ Validation error at root: Additional properties are not allowed ('extra_field' was unexpected)
```

## Relationship to Existing Validation

The JSON Schema is **complementary** to existing validation:

```python
# sketcher/model.py - Current validation
model = Model("skewer.yaml")
model.check()  # ✅ Validates structure and references

# JSON Schema validation (optional)
import json
import jsonschema

schema = json.load(open("skewer-schema.json"))
data = yaml.safe_load(open("skewer.yaml"))
jsonschema.validate(data, schema)  # ✅ Additional validation layer
```

**Current `.check()` validation:**
- Deferred (runs after parsing)
- Allows `@default@` substitution first
- Custom error messages
- Used by all Sketcher commands

**JSON Schema validation:**
- Immediate (fails at parse time)
- Stricter (rejects unknown fields)
- Detailed error paths
- Optional pre-validation step

Both approaches can coexist:
1. JSON Schema catches typos and structure errors early
2. `.check()` validates resolved references and runtime requirements

## Schema Maintenance

When adding new fields to `skewer.yaml`:

1. **Update the schema** (`skewer-schema.json`):
   ```json
   {
     "properties": {
       "new_field": {
         "type": "string",
         "description": "Description of new field"
       }
     }
   }
   ```

2. **Update Python model** (`sketcher/model.py`):
   ```python
   new_field = object_property("new_field")
   ```

3. **Update Go model** (`internal/model/model.go`):
   ```go
   NewField string `yaml:"new_field"`
   ```

4. **Test validation**:
   ```bash
   python scripts/validate-schema.py tests/fixtures/skewer-resolved.yaml
   ```

5. **Update documentation** (`README.md`, this file)

## Benefits of JSON Schema

- ✅ **IDE autocomplete** - YAML language servers provide suggestions
- ✅ **Early error detection** - Catch typos before running Sketcher
- ✅ **Self-documenting** - Schema describes expected structure
- ✅ **Cross-tool validation** - Same schema for Python, Go, editors, CI/CD
- ✅ **Version control** - Schema changes are tracked in git
- ✅ **External tool integration** - Other tools can consume the schema

## Limitations

- ⚠️ **Does not validate `@default@` substitution** - Placeholders are allowed in strings
- ⚠️ **Does not resolve `standard:` references** - Use `sketcher resolve` first
- ⚠️ **Does not validate site name references** - Step commands can reference unknown sites
- ⚠️ **Does not check kubeconfig file existence** - Only validates path format

For complete validation, use both JSON Schema + Sketcher's `.check()`.

## Further Reading

- [JSON Schema Documentation](https://json-schema.org/)
- [Understanding JSON Schema](https://json-schema.org/understanding-json-schema/)
- [YAML Schemas in VS Code](https://code.visualstudio.com/docs/languages/json#_json-schemas-and-settings)
- [Sketcher README](./README.md)
- [Schema Modeling Analysis](./schema.md)
