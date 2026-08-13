# JSON Schema Implementation Summary

This document summarizes the JSON Schema implementation for Sketcher's `skewer.yaml` configuration files.

## What Was Created

### 1. JSON Schema Definition
**File:** `skewer-schema.json`

A comprehensive JSON Schema (draft-07) that defines:
- Required and optional fields for `skewer.yaml`
- Platform-specific conditional validation
- Field type validation (string, boolean, integer, enum)
- Pattern matching (namespace, resource names)
- Range validation (port numbers)
- Rejection of unknown fields

### 2. Validation Tools

**Python Validator** (`scripts/validate-schema.py`):
- Full JSON Schema validation
- Detailed error messages with field paths
- Batch validation support
- Recommended for CI/CD

**Go Validator** (`scripts/validate-schema.go`):
- Native Go implementation
- Requires `github.com/xeipuuv/gojsonschema`
- Compiles to standalone binary

**Shell Script** (`scripts/validate-schema.sh`):
- Basic YAML syntax checking
- Requires `yq` and `jq`
- Checks for required fields only

### 3. Documentation

**`SCHEMA.md`**:
- Complete guide to using JSON Schema validation
- IDE integration instructions (VS Code, JetBrains, Neovim)
- CI/CD integration examples (GitHub Actions, GitLab)
- Error examples and troubleshooting
- Schema maintenance guide

**`schema.md`**:
- Analysis of schema modeling approaches
- Python vs Go implementation comparison
- Recommendations for each language
- Pros/cons of alternatives (Pydantic, dataclasses, attrs, struct tags)

### 4. Example Files

**`examples/minimal-valid.yaml`**:
- Minimal valid example for testing
- Demonstrates required fields

**`examples/invalid-example.yaml`**:
- Intentionally invalid example
- Shows common validation errors

### 5. Build Integration

**`justfile` recipes**:
```bash
just validate skewer.yaml              # Validate single file
just validate examples/*.yaml          # Validate multiple files
just validate-examples                 # Validate known-good examples
just validate-verbose skewer.yaml      # Show all errors
```

## Quick Start

```bash
# Install dependencies
pip install jsonschema

# Validate a file
python scripts/validate-schema.py skewer.yaml

# Validate all examples
just validate-examples

# Test with minimal valid example
python scripts/validate-schema.py examples/minimal-valid.yaml
```

## Key Features

### Schema Capabilities

✅ **Structural Validation**
- Required fields: `title`, `sites`, `steps`
- Type checking: strings, booleans, integers, arrays, objects
- Minimum constraints: at least 1 site, at least 1 step

✅ **Platform Validation**
- Valid platforms: `kubernetes`, `podman`, `docker`, `linux`
- Conditional requirements based on platform
- Environment variable validation

✅ **Kubernetes-Specific**
- Namespace required for `platform: kubernetes`
- `KUBECONFIG` environment variable required
- Namespace naming follows DNS-1123 rules (lowercase, alphanumeric, hyphens)

✅ **Podman/Docker/Linux-Specific**
- `SKUPPER_PLATFORM` environment variable required
- Must match one of: `podman`, `docker`, `linux`

✅ **Command Validation**
- `apply` field restricted to: `readme`, `test`
- Port range validation: 1-65535
- Resource format validation: `type/name`

✅ **Strict Mode**
- Rejects unknown/unexpected fields
- Helps catch typos early
- Prevents configuration drift

### Error Examples

**Missing required field:**
```
✗ Validation error at root: 'title' is a required property
```

**Invalid platform:**
```
✗ Validation error at sites → west → platform: 'k8s' is not one of ['kubernetes', 'podman', 'docker', 'linux']
```

**Unknown field:**
```
✗ Validation error at root: Additional properties are not allowed ('extra_field' was unexpected)
```

**Invalid namespace format:**
```
✗ Validation error at sites → west → namespace: 'MyNamespace' does not match '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
```

## IDE Integration

### VS Code

Add to `.vscode/settings.json`:
```json
{
  "yaml.schemas": {
    "./skewer-schema.json": ["**/skewer.yaml", "**/skewer-*.yaml"]
  }
}
```

Benefits:
- Autocomplete for field names
- Inline validation errors
- Hover documentation
- Enum value suggestions

### JetBrains IDEs

Settings → Languages & Frameworks → Schemas and DTDs → JSON Schema Mappings

Benefits same as VS Code.

## CI/CD Integration

### GitHub Actions

```yaml
- name: Validate skewer.yaml
  run: |
    pip install jsonschema
    python scripts/validate-schema.py skewer.yaml
```

### Pre-commit Hook

```bash
#!/bin/bash
if [ -f "skewer.yaml" ]; then
    python scripts/validate-schema.py skewer.yaml || exit 1
fi
```

## Relationship to Existing Validation

### Current Validation (`.check()`)
- Deferred until after parsing
- Allows `@default@` substitution first
- Custom error messages
- Validates site name references in steps
- Used by all Sketcher commands

### JSON Schema Validation
- Immediate (fails at parse time)
- Stricter (rejects unknown fields)
- Detailed error paths
- Cross-tool compatible
- Optional pre-validation layer

### Recommended Workflow

```python
# 1. Optional: JSON Schema pre-validation (catch typos early)
import jsonschema
schema = json.load(open("skewer-schema.json"))
data = yaml.safe_load(open("skewer.yaml"))
jsonschema.validate(data, schema)

# 2. Standard Sketcher validation (always runs)
model = Model("skewer.yaml")
model.check()
```

Or in CI/CD:
```bash
# Pre-validate with schema
python scripts/validate-schema.py skewer.yaml

# Run full test
python -m sketcher test skewer.yaml
```

## Limitations

The JSON Schema **does not** validate:

❌ `@default@` placeholder substitution (allows any string)
❌ `standard:` step references (use `sketcher resolve` first)
❌ Site name references in step commands (allows unknown sites)
❌ File existence (kubeconfig paths, etc.)
❌ Network reachability
❌ Kubernetes cluster connectivity

For complete validation, use **both** JSON Schema + Sketcher's `.check()`.

## Design Decisions

### Why JSON Schema?

**Chosen:**
- Industry standard (widely supported)
- IDE integration (VS Code, JetBrains, etc.)
- Cross-language validation
- Self-documenting
- Tooling ecosystem (validators, generators, linters)

**Not chosen:**
- Custom DSL (too much work, no tooling)
- XML Schema (verbose, outdated)
- Protocol Buffers (not designed for YAML)
- YAML Schema (not standardized)

### Why Optional Validation?

The schema is **optional** because:
- Existing validation works well
- Zero-dependency philosophy (PyYAML only)
- `@default@` substitution requires custom logic
- Legacy compatibility (existing yamls work unchanged)

Benefits of keeping it optional:
- No breaking changes
- Gradual adoption
- Can be used in CI without changing code
- IDE users benefit immediately

### Why Not Replace Current Validation?

Current property descriptor pattern:
- Zero dependencies
- Proven (63 tests, production use)
- Handles `@default@` substitution
- Lazy validation (allows parsing before checking)

JSON Schema would require:
- Adding `jsonschema` dependency (against project goals)
- Custom handling for `@default@` placeholders
- Pre-processing before validation
- More complex error handling

**Decision:** Keep both. JSON Schema for IDE/CI, property descriptors for runtime.

## Future Enhancements

### Possible Additions

1. **JSON Schema for resolved vs unresolved YAML**
   - `skewer-schema.json` (current - resolved only)
   - `skewer-schema-unresolved.json` (allows `standard:` references)

2. **Custom validators for `@default@`**
   ```python
   def validate_with_placeholders(data, schema):
       # Strip @default@ before validation
       cleaned = strip_placeholders(data)
       jsonschema.validate(cleaned, schema)
   ```

3. **Site reference validation**
   ```json
   {
     "properties": {
       "steps": {
         "items": {
           "properties": {
             "commands": {
               "propertyNames": {
                 "$ref": "#/definitions/SiteName"
               }
             }
           }
         }
       }
     }
   }
   ```

4. **Schema versioning**
   ```json
   {
     "$id": "https://skupper.io/schemas/skewer/v1.0.0.json",
     "version": "1.0.0"
   }
   ```

5. **Auto-generated documentation**
   ```bash
   # Generate markdown docs from schema
   generate-schema-docs skewer-schema.json > docs/schema-reference.md
   ```

### Not Recommended

❌ Replacing current validation entirely (loses `@default@` support)
❌ Making validation mandatory (breaking change)
❌ Adding Pydantic dependency (against project goals)

## Testing

### Validation Script Tests

```bash
# Valid files should pass
python scripts/validate-schema.py examples/minimal-valid.yaml
# ✓ Valid

# Invalid files should fail
python scripts/validate-schema.py examples/invalid-example.yaml
# ✗ Validation error at root: Additional properties are not allowed

# Resolved fixtures should pass
python scripts/validate-schema.py tests/fixtures/skewer-resolved.yaml
# ✓ Valid

# Unresolved fixtures should fail (contains 'standard:' references)
python scripts/validate-schema.py tests/fixtures/skewer.yaml
# ✗ Validation error at steps → X: 'title' is a required property
```

### Integration Tests

Add to test suite:
```python
def test_schema_validation():
    """Test that resolved YAML passes schema validation."""
    import jsonschema
    
    schema = json.load(open("skewer-schema.json"))
    data = yaml.safe_load(open("tests/fixtures/skewer-resolved.yaml"))
    
    # Should not raise
    jsonschema.validate(data, schema)
```

## Maintenance Checklist

When adding a new field to `skewer.yaml`:

- [ ] Update `skewer-schema.json`
- [ ] Update Python model (`sketcher/model.py`)
- [ ] Update Go model (`internal/model/model.go`)
- [ ] Test with `just validate-examples`
- [ ] Update `README.md` documentation
- [ ] Update `SCHEMA.md` if needed
- [ ] Add to test fixtures if necessary

## Files Created

```
skewer-schema.json              # JSON Schema definition
scripts/validate-schema.py      # Python validator (recommended)
scripts/validate-schema.go      # Go validator
scripts/validate-schema.sh      # Shell script (basic checks)
SCHEMA.md                       # User guide
schema.md                       # Technical analysis
docs/json-schema-summary.md     # This file
examples/minimal-valid.yaml     # Minimal valid example
examples/invalid-example.yaml   # Invalid example for testing
```

Updated files:
```
justfile                        # Added validation recipes
```

## Resources

- [JSON Schema Official Site](https://json-schema.org/)
- [Understanding JSON Schema](https://json-schema.org/understanding-json-schema/)
- [VS Code YAML Extension](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)
- [jsonschema Python Package](https://pypi.org/project/jsonschema/)
- [gojsonschema Go Package](https://github.com/xeipuuv/gojsonschema)

## Summary

✅ **Created comprehensive JSON Schema for skewer.yaml**
✅ **Validation tools for Python, Go, and shell**
✅ **Documentation and examples**
✅ **IDE integration support**
✅ **CI/CD ready**
✅ **Optional, non-breaking addition**
✅ **Complements existing validation**

The JSON Schema provides an optional validation layer that catches errors early, integrates with IDEs, and works across tools—while preserving the simplicity and zero-dependency philosophy of the existing implementation.
