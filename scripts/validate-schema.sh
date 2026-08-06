#!/bin/bash
# Validate skewer.yaml files against the JSON Schema using Go
#
# Usage:
#   ./scripts/validate-schema.sh skewer.yaml
#   ./scripts/validate-schema.sh examples/*.yaml

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_PATH="$SCRIPT_DIR/../skewer-schema.json"

if [ $# -lt 1 ]; then
    echo "Usage: validate-schema.sh <yaml-file> [yaml-file ...]" >&2
    echo "" >&2
    echo "Example:" >&2
    echo "  ./scripts/validate-schema.sh skewer.yaml" >&2
    echo "  ./scripts/validate-schema.sh examples/*.yaml" >&2
    exit 1
fi

if [ ! -f "$SCHEMA_PATH" ]; then
    echo "Error: Schema not found at $SCHEMA_PATH" >&2
    exit 1
fi

# Check if jq and yq are available (for basic validation)
if ! command -v yq &> /dev/null; then
    echo "Error: yq not found. Install with: go install github.com/mikefarah/yq/v4@latest" >&2
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "Error: jq not found. Install from: https://stedolan.github.io/jq/download/" >&2
    exit 1
fi

# Note: Full JSON Schema validation in pure bash/Go is complex
# For production use, consider:
# 1. Python script (validate-schema.py) - full validation
# 2. Go tool with github.com/xeipuuv/gojsonschema
# 3. Online validators

echo "Note: This script performs basic YAML syntax validation only."
echo "For full JSON Schema validation, use: python scripts/validate-schema.py"
echo ""

failed=0
for yaml_file in "$@"; do
    if [ ! -f "$yaml_file" ]; then
        echo "✗ $yaml_file: File not found"
        failed=1
        continue
    fi

    # Basic YAML syntax check
    if yq eval '.' "$yaml_file" > /dev/null 2>&1; then
        # Check for required fields
        title=$(yq eval '.title' "$yaml_file")
        sites=$(yq eval '.sites' "$yaml_file")
        steps=$(yq eval '.steps' "$yaml_file")

        if [ "$title" = "null" ] || [ -z "$title" ]; then
            echo "✗ $yaml_file: Missing required field 'title'"
            failed=1
        elif [ "$sites" = "null" ] || [ -z "$sites" ]; then
            echo "✗ $yaml_file: Missing required field 'sites'"
            failed=1
        elif [ "$steps" = "null" ] || [ -z "$steps" ]; then
            echo "✗ $yaml_file: Missing required field 'steps'"
            failed=1
        else
            echo "✓ $yaml_file: Valid YAML with required fields"
        fi
    else
        echo "✗ $yaml_file: Invalid YAML syntax"
        failed=1
    fi
done

if [ $failed -eq 1 ]; then
    echo ""
    echo "Some files failed validation."
    echo "For detailed validation, use: python scripts/validate-schema.py $*"
    exit 1
fi

echo ""
echo "✓ All files passed basic validation"
echo "For full JSON Schema validation, use: python scripts/validate-schema.py $*"
