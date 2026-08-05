#!/usr/bin/env python3
"""
Validate skewer.yaml files against the JSON Schema.

Usage:
    python scripts/validate-schema.py skewer.yaml
    python scripts/validate-schema.py examples/*.yaml
"""

import sys
import json
from pathlib import Path

try:
    import yaml
    from jsonschema import validate, ValidationError, SchemaError
except ImportError:
    print("Error: Required packages not installed.", file=sys.stderr)
    print("Install with: pip install pyyaml jsonschema", file=sys.stderr)
    sys.exit(1)


def load_schema(schema_path: Path) -> dict:
    """Load the JSON schema."""
    with open(schema_path) as f:
        return json.load(f)


def load_yaml(yaml_path: Path) -> dict:
    """Load a YAML file."""
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def validate_file(yaml_path: Path, schema: dict) -> tuple[bool, str]:
    """
    Validate a YAML file against the schema.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        data = load_yaml(yaml_path)
        validate(instance=data, schema=schema)
        return True, "✓ Valid"
    except ValidationError as e:
        # Format the validation error nicely
        path = " → ".join(str(p) for p in e.path) if e.path else "root"
        return False, f"✗ Validation error at {path}: {e.message}"
    except SchemaError as e:
        return False, f"✗ Schema error: {e.message}"
    except yaml.YAMLError as e:
        return False, f"✗ YAML parsing error: {e}"
    except Exception as e:
        return False, f"✗ Unexpected error: {e}"


def main():
    if len(sys.argv) < 2:
        print("Usage: validate-schema.py <yaml-file> [yaml-file ...]", file=sys.stderr)
        print("\nExample:", file=sys.stderr)
        print("  python scripts/validate-schema.py skewer.yaml", file=sys.stderr)
        print("  python scripts/validate-schema.py examples/*.yaml", file=sys.stderr)
        sys.exit(1)

    # Load schema
    script_dir = Path(__file__).parent
    schema_path = script_dir.parent / "skewer-schema.json"

    if not schema_path.exists():
        print(f"Error: Schema not found at {schema_path}", file=sys.stderr)
        sys.exit(1)

    try:
        schema = load_schema(schema_path)
    except Exception as e:
        print(f"Error loading schema: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate each file
    yaml_files = [Path(arg) for arg in sys.argv[1:]]
    results = []

    for yaml_path in yaml_files:
        if not yaml_path.exists():
            results.append((yaml_path, False, f"✗ File not found: {yaml_path}"))
            continue

        success, message = validate_file(yaml_path, schema)
        results.append((yaml_path, success, message))

    # Print results
    max_path_len = max(len(str(p)) for p, _, _ in results)

    for yaml_path, success, message in results:
        path_str = str(yaml_path).ljust(max_path_len)
        print(f"{path_str}  {message}")

    # Exit with error if any validation failed
    if any(not success for _, success, _ in results):
        sys.exit(1)

    print(f"\n✓ All {len(results)} file(s) valid")
    sys.exit(0)


if __name__ == "__main__":
    main()
