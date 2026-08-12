# Sketcher Scripts

Utility scripts for maintaining and validating Skupper example YAML files.

## Quick Start

### Reformat All Examples (Recommended)

```bash
# Preview changes without modifying files
./scripts/reformat-all.sh --dry-run

# Reformat all YAML files
./scripts/reformat-all.sh

# Reformat and generate markdown in one step
./scripts/reformat-all.sh --generate-md

# Just validate all files
./scripts/reformat-all.sh --validate
```

---

## Individual Scripts

## validate-schema.py

Validates skewer.yaml files against the JSON Schema.

### Usage

```bash
# Validate a single file
python scripts/validate-schema.py skewer.yaml

# Validate multiple files
python scripts/validate-schema.py examples/*.yaml

# From project root with venv
source .venv/bin/activate
python scripts/validate-schema.py examples/skupper-example-hello-world.yaml
```

### Requirements

```bash
pip install pyyaml jsonschema
```

## reformat_yaml.py

Reformats YAML files to use clean literal block style (`|`) instead of escaped newlines and quoted strings.

### Features

- Validates files before and after reformatting against schema
- Uses literal block style for multi-line strings
- Preserves proper indentation
- Supports dry-run mode
- Safe: only reformats files that are valid before and after

### Usage

```bash
# Dry run to preview changes
python scripts/reformat_yaml.py --dry-run examples/*.yaml

# Reformat files
python scripts/reformat_yaml.py examples/*.yaml

# Custom schema location
python scripts/reformat_yaml.py --schema path/to/schema.json examples/*.yaml

# From project root with venv
source .venv/bin/activate
python scripts/reformat_yaml.py examples/skupper-example-hello-world.yaml
```

### Example Transformation

**Before:**
```yaml
overview: "This example is a very simple application\ndeployed across clusters.\n\n\
  It contains two services:\n\n* A backend service..."
```

**After:**
```yaml
overview: |
  This example is a very simple application
  deployed across clusters.

  It contains two services:

  * A backend service...
```

### Requirements

```bash
pip install pyyaml jsonschema
```

Or install dev dependencies:

```bash
pip install -e ".[dev]"
```

## reformat-all.sh

All-in-one script to reformat all YAML files and optionally generate markdown.

### Features

- Automatically activates virtual environment
- Reformats all example YAML files
- Optional markdown generation
- Optional validation-only mode
- Colored output for easy reading
- Safe: validates before and after reformatting

### Usage

```bash
# Basic usage - reformat all YAML files
./scripts/reformat-all.sh

# Preview changes (dry run)
./scripts/reformat-all.sh --dry-run

# Reformat and generate markdown
./scripts/reformat-all.sh --generate-md

# Validate all files without reformatting
./scripts/reformat-all.sh --validate

# Show help
./scripts/reformat-all.sh --help
```

### Options

- `--dry-run` - Show what would change without modifying files
- `--generate-md` - Also generate README.md files after reformatting
- `--validate` - Only validate files against schema, don't reformat
- `-h, --help` - Show help message

### Requirements

Script will automatically:
- Create virtual environment if missing
- Install dependencies if needed
- Activate venv before running
