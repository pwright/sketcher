# JSON Schema Quick Start

**Catch `skewer.yaml` errors before running Sketcher.**

## What You'll Accomplish

In 5 minutes, you'll be able to:
- Validate `skewer.yaml` syntax and structure instantly
- Get autocomplete and inline errors in your IDE
- Block invalid YAML from reaching CI/CD

**Why this helps**: Schema validation catches typos, missing fields, and invalid values at edit time instead of test time.

---

## 1. Install and Validate

```bash
# Install validator (one dependency)
pip install jsonschema
```

## 2. Validate Your skewer.yaml

```bash
# Validate the minimal example
python scripts/validate-schema.py examples/minimal-valid.yaml
```

Output:
```
examples/minimal-valid.yaml  ✓ Valid

✓ All 1 file(s) valid
```

**What this tells you**: Your `skewer.yaml` structure is correct, all required fields are present, and field types match expectations.

---

## 3. Catch Errors Early

Create a file with an error to see validation in action:

```bash
# This will show validation errors
python scripts/validate-schema.py examples/invalid-example.yaml
```

Output:
```
examples/invalid-example.yaml  ✗ Validation error at root: Additional properties are not allowed ('extra_field' was unexpected)
```

**What this prevents**: Wasting time running clusters and tests only to discover a typo or missing field.

---

## 4. Validate Multiple Files at Once

```bash
# Using Python script
python scripts/validate-schema.py examples/minimal-valid.yaml tests/fixtures/skewer-resolved.yaml

# Or using justfile
just validate examples/minimal-valid.yaml tests/fixtures/skewer-resolved.yaml
```

---

## 5. Get IDE Autocomplete (Optional but Recommended)

**What you'll gain**: Autocomplete for field names, inline validation errors, hover documentation, and enum suggestions.

### VS Code

Create or update `.vscode/settings.json`:
```json
{
  "yaml.schemas": {
    "./skewer-schema.json": ["**/skewer.yaml", "**/skewer-*.yaml"]
  }
}
```

**Result**: As you type `skewer.yaml`, VS Code suggests valid field names, shows errors inline, and displays documentation on hover.

---

## Reference: Common Commands

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

---

## What You've Accomplished

You can now:
- ✅ Validate `skewer.yaml` files before running Sketcher
- ✅ Catch typos, missing fields, and invalid values at edit time
- ✅ Get autocomplete and inline errors in your IDE (if configured)
- ✅ Integrate validation into pre-commit hooks and CI/CD pipelines

---

## Next Steps

**Learn more about validation**:
- [Schema Documentation](../development/schema.md) - Complete field reference and validation rules
- [Schema Summary](./json-schema-summary.md) - Implementation details

**Troubleshoot issues**:
- [Use Cases](../user-guide/use-cases.md) - Platform-specific workflows and troubleshooting
- [Sketcher Documentation](../index.md) - Full Sketcher documentation

---

## Common Questions

**Schema validation failing?**
- Check the error message for the exact field path
- Compare your YAML with `examples/minimal-valid.yaml`
- Ensure file is resolved (no `standard:` references) - run `skewer resolve` first

**Schema validation passes but Sketcher fails?**
- The schema doesn't validate everything (site references, file existence, runtime requirements)
- Run `skewer generate skewer.yaml` for full validation
- Schema validation is an optional early-detection layer, not a replacement for Sketcher's validation

**Want to disable validation?**
- Simply don't run the validation script - it's completely optional
- Remove `.vscode/settings.json` YAML schema configuration to disable IDE validation

---

## About This Guide

This quick start uses the **Explore** action from the Seven-Action Documentation Model - it helps you try JSON Schema validation with minimal commitment (5 minutes, one dependency) to see if it fits your workflow. For complete field reference and integration patterns, see [Schema Documentation](../development/schema.md).
