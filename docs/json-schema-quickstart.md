# JSON Schema Quick Start

Get started with JSON Schema validation for `skewer.yaml` in 5 minutes.

## 1. Install Dependencies

```bash
pip install jsonschema
```

That's it! Only one dependency needed.

## 2. Validate Your First File

```bash
# Validate the minimal example
python scripts/validate-schema.py examples/minimal-valid.yaml
```

Output:
```
examples/minimal-valid.yaml  ✓ Valid

✓ All 1 file(s) valid
```

## 3. Try an Invalid File

```bash
# This will show validation errors
python scripts/validate-schema.py examples/invalid-example.yaml
```

Output:
```
examples/invalid-example.yaml  ✗ Validation error at root: Additional properties are not allowed ('extra_field' was unexpected)
```

## 4. Validate Multiple Files

```bash
# Using Python script
python scripts/validate-schema.py examples/minimal-valid.yaml tests/fixtures/skewer-resolved.yaml

# Or using justfile
just validate examples/minimal-valid.yaml tests/fixtures/skewer-resolved.yaml
```

## 5. Enable IDE Autocomplete (Optional)

### VS Code

Create `.vscode/settings.json`:
```json
{
  "yaml.schemas": {
    "./skewer-schema.json": ["**/skewer.yaml", "**/skewer-*.yaml"]
  }
}
```

Now you get:
- ✅ Autocomplete for field names
- ✅ Inline validation errors
- ✅ Hover documentation
- ✅ Enum suggestions

## Common Commands

```bash
# Single file
python scripts/validate-schema.py skewer.yaml

# Multiple files
python scripts/validate-schema.py examples/*.yaml

# Using justfile (shorter)
just validate skewer.yaml
just validate examples/*.yaml
just validate-examples

# Resolve then validate (for files with 'standard:' references)
python -m sketcher resolve skewer.yaml -o skewer-resolved.yaml
python scripts/validate-schema.py skewer-resolved.yaml
```

## What Gets Validated?

✅ **Required fields**
- `title` is present and not empty
- `sites` has at least one site
- `steps` has at least one step

✅ **Field types**
- Strings, booleans, integers are correct types
- Arrays and objects match expected structure

✅ **Platform validation**
- Platform is one of: `kubernetes`, `podman`, `docker`, `linux`
- Kubernetes sites have `namespace` and `KUBECONFIG`
- Podman/Docker/Linux sites have `SKUPPER_PLATFORM`

✅ **Command validation**
- `apply` field is either `readme` or `test`
- Port numbers are 1-65535
- Resource formats match `type/name`

✅ **No unknown fields**
- Extra/misspelled fields are rejected

## Common Validation Errors

### Missing Required Field

**Error:**
```
✗ Validation error at root: 'title' is a required property
```

**Fix:**
```yaml
title: My Example  # Add missing title
sites:
  # ...
```

### Invalid Platform

**Error:**
```
✗ Validation error at sites → west → platform: 'k8s' is not one of ['kubernetes', 'podman', 'docker', 'linux']
```

**Fix:**
```yaml
sites:
  west:
    platform: kubernetes  # Use full name, not abbreviation
```

### Unknown Field

**Error:**
```
✗ Validation error at root: Additional properties are not allowed ('extra_field' was unexpected)
```

**Fix:**
```yaml
title: My Example
# extra_field: value  # Remove or rename unknown field
sites:
  # ...
```

### Invalid Namespace

**Error:**
```
✗ Validation error at sites → west → namespace: 'MyNamespace' does not match '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
```

**Fix:**
```yaml
sites:
  west:
    namespace: my-namespace  # Use lowercase and hyphens only
```

## Integration with Existing Workflow

The JSON Schema validation is **optional** and works alongside existing Sketcher commands:

```bash
# 1. (Optional) Validate with schema first
python scripts/validate-schema.py skewer.yaml

# 2. Generate README (existing workflow)
python -m sketcher generate skewer.yaml

# 3. Run demo (existing workflow)
python -m sketcher demo skewer.yaml

# 4. Run tests (existing workflow)
python -m sketcher test skewer.yaml
```

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/validate.yml`:
```yaml
name: Validate
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install jsonschema
      - run: python scripts/validate-schema.py skewer.yaml
```

### Pre-commit Hook

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
if [ -f skewer.yaml ]; then
    python scripts/validate-schema.py skewer.yaml || exit 1
fi
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Resolved vs Unresolved YAML

**Important:** The schema validates **resolved** YAML only.

If your `skewer.yaml` contains `standard:` references:
```yaml
steps:
  - standard: platform/access_your_kubernetes_clusters  # ❌ Won't validate
```

First resolve it:
```bash
# Resolve
python -m sketcher resolve skewer.yaml -o skewer-resolved.yaml

# Then validate
python scripts/validate-schema.py skewer-resolved.yaml
```

Resolved YAML has expanded steps:
```yaml
steps:
  - title: Configure separate console sessions  # ✅ Validates
    commands:
      west:
        - run: export KUBECONFIG=~/.kube/config-west
```

## Next Steps

- Read [`SCHEMA.md`](../SCHEMA.md) for complete documentation
- Read [`schema.md`](../schema.md) for technical analysis
- Read [`docs/json-schema-summary.md`](./json-schema-summary.md) for implementation details
- Check [`skewer-schema.json`](../skewer-schema.json) for schema definition

## Help

**Schema validation failing?**
- Check error message for field path
- Compare with `examples/minimal-valid.yaml`
- Ensure file is resolved (no `standard:` references)

**Schema validation passing but Sketcher failing?**
- The schema doesn't validate everything (site references, file existence, etc.)
- Run `python -m sketcher generate skewer.yaml` for full validation

**Want to disable validation?**
- Just don't run the validation script
- The schema is optional and non-intrusive

**Questions?**
- Open an issue on GitHub
- Check existing documentation
- Look at example files in `examples/`
