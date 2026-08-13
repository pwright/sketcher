#!/usr/bin/env python3
"""
Reformat YAML files to use literal block style (|) instead of quoted strings with \n.
This provides cleaner, more readable YAML formatting.

Validates files against skewer-schema.json before and after reformatting.
"""

import sys
import yaml
import json
import argparse
from pathlib import Path
from typing import Any, Dict, Tuple

try:
    from jsonschema import validate, ValidationError, SchemaError
except ImportError:
    print("Error: jsonschema not installed.", file=sys.stderr)
    print("Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(1)


class LiteralString(str):
    """Custom string type to indicate literal block style should be used."""
    pass


def literal_presenter(dumper, data):
    """Custom YAML presenter for multi-line strings using literal block style (|)."""
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


def convert_multiline_strings(obj: Any) -> Any:
    """Recursively convert multi-line strings to LiteralString type."""
    if isinstance(obj, dict):
        return {k: convert_multiline_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_multiline_strings(item) for item in obj]
    elif isinstance(obj, str) and '\n' in obj:
        return LiteralString(obj)
    return obj


def validate_against_schema(data: Any, schema: Dict) -> Tuple[bool, str]:
    """
    Validate data against JSON schema.

    Returns:
        Tuple of (success: bool, error_message: str)
    """
    try:
        validate(instance=data, schema=schema)
        return True, ""
    except ValidationError as e:
        path = " → ".join(str(p) for p in e.path) if e.path else "root"
        return False, f"Validation error at {path}: {e.message}"
    except SchemaError as e:
        return False, f"Schema error: {e.message}"


def reformat_yaml_file(input_path: Path, schema: Dict, dry_run: bool = False) -> bool:
    """
    Reformat a YAML file to use literal block style.

    Args:
        input_path: Path to the YAML file
        schema: JSON schema to validate against
        dry_run: If True, only show what would be changed

    Returns:
        True if file was modified (or would be modified in dry_run)
    """
    try:
        # Read the original file
        with open(input_path, 'r') as f:
            original_content = f.read()

        # Parse YAML
        data = yaml.safe_load(original_content)

        # Validate original data
        valid, error = validate_against_schema(data, schema)
        if not valid:
            print(f"⚠ Skipping {input_path}: Invalid before reformatting: {error}", file=sys.stderr)
            return False

        # Convert multi-line strings
        data = convert_multiline_strings(data)

        # Set up custom representer
        yaml.add_representer(LiteralString, literal_presenter)

        # Dump with clean formatting
        new_content = yaml.dump(
            data,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=80,
            indent=2
        )

        # Parse reformatted content and validate
        reformatted_data = yaml.safe_load(new_content)
        valid, error = validate_against_schema(reformatted_data, schema)
        if not valid:
            print(f"⚠ Skipping {input_path}: Would be invalid after reformatting: {error}", file=sys.stderr)
            return False

        # Check if content changed
        if original_content == new_content:
            return False

        if dry_run:
            print(f"Would reformat: {input_path}")
            return True

        # Write reformatted content
        with open(input_path, 'w') as f:
            f.write(new_content)

        print(f"✓ Reformatted: {input_path}")
        return True

    except Exception as e:
        print(f"Error processing {input_path}: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Reformat YAML files to use literal block style (|)'
    )
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='YAML files to reformat'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--schema',
        type=Path,
        help='Path to JSON schema (default: skewer-schema.json in project root)'
    )

    args = parser.parse_args()

    # Load schema
    if args.schema:
        schema_path = args.schema
    else:
        script_dir = Path(__file__).parent
        schema_path = script_dir.parent / "skewer-schema.json"

    if not schema_path.exists():
        print(f"Error: Schema not found at {schema_path}", file=sys.stderr)
        print("Specify schema with --schema option", file=sys.stderr)
        return 1

    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except Exception as e:
        print(f"Error loading schema: {e}", file=sys.stderr)
        return 1

    # Reformat files
    modified_count = 0
    for file_path in args.files:
        if not file_path.exists():
            print(f"File not found: {file_path}", file=sys.stderr)
            continue

        if reformat_yaml_file(file_path, schema, args.dry_run):
            modified_count += 1

    action = "Would reformat" if args.dry_run else "Reformatted"
    print(f"\n{action} {modified_count} file(s)")

    return 0


if __name__ == '__main__':
    sys.exit(main())
