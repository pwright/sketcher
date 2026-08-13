#!/bin/bash
# Reformat all YAML example files to use literal block style

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
DRY_RUN=false
GENERATE_MD=false
VALIDATE_ONLY=false
GENERATE_ONLY=false

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Reformat all YAML example files to use clean literal block style (|)

OPTIONS:
    --dry-run         Show what would be changed without modifying files
    --generate-md     Also generate README.md files after reformatting
    --generate-only   Only generate markdown files, skip reformatting
    --validate        Only validate files, don't reformat
    -h, --help        Show this help message

EXAMPLES:
    $0                          # Reformat all YAML files
    $0 --dry-run                # Preview changes
    $0 --generate-md            # Reformat and generate markdown
    $0 --generate-only          # Just generate markdown from existing YAML
    $0 --validate               # Just validate against schema

EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --generate-md)
            GENERATE_MD=true
            shift
            ;;
        --generate-only)
            GENERATE_ONLY=true
            shift
            ;;
        --validate)
            VALIDATE_ONLY=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Warning: .venv not found. Creating virtual environment...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -e ".[dev]"
else
    source .venv/bin/activate
fi

echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}Sketcher YAML Reformatter${NC}"
echo -e "${BLUE}==================================================================${NC}"
echo

# Validate only mode
if [ "$VALIDATE_ONLY" = true ]; then
    echo -e "${BLUE}Validating all YAML files...${NC}"
    echo
    python3 scripts/validate-schema.py examples/*.yaml
    echo
    echo -e "${GREEN}✓ Validation complete${NC}"
    exit 0
fi

# Generate only mode
if [ "$GENERATE_ONLY" = true ]; then
    echo -e "${BLUE}Generating Markdown Documentation Only${NC}"
    echo -e "${BLUE}---------------------------------------${NC}"
    echo

    COUNT=0
    ERRORS=0

    for yaml_file in examples/skupper-example-*.yaml; do
        if [ -f "$yaml_file" ]; then
            basename="$(basename "$yaml_file" .yaml)"
            output_file="examples/${basename}.md"
            echo -n "  Processing $basename... "

            if skewer generate "$yaml_file" -o "$output_file" 2>&1 | grep -q "Generated"; then
                echo -e "${GREEN}✓${NC}"
                COUNT=$((COUNT + 1))
            else
                echo -e "${YELLOW}⚠${NC}"
                ERRORS=$((ERRORS + 1))
            fi
        fi
    done

    echo
    echo -e "${GREEN}✓ Generated markdown for $COUNT files${NC}"
    if [ $ERRORS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $ERRORS files had warnings or errors${NC}"
    fi

    echo
    echo -e "${BLUE}==================================================================${NC}"
    echo -e "${GREEN}Markdown generation complete!${NC}"
    echo -e "${BLUE}==================================================================${NC}"
    exit 0
fi

# Reformat mode
REFORMAT_ARGS=""
if [ "$DRY_RUN" = true ]; then
    REFORMAT_ARGS="--dry-run"
    echo -e "${YELLOW}DRY RUN MODE - No files will be modified${NC}"
    echo
fi

echo -e "${BLUE}Step 1: Reformatting YAML files${NC}"
echo -e "${BLUE}----------------------------------${NC}"
echo

python3 scripts/reformat_yaml.py $REFORMAT_ARGS examples/*.yaml

echo
echo -e "${GREEN}✓ YAML reformatting complete${NC}"

if [ "$DRY_RUN" = true ]; then
    echo
    echo -e "${YELLOW}This was a dry run. Use without --dry-run to apply changes.${NC}"
    exit 0
fi

# Generate markdown if requested
if [ "$GENERATE_MD" = true ]; then
    echo
    echo -e "${BLUE}Step 2: Generating Markdown Documentation${NC}"
    echo -e "${BLUE}------------------------------------------${NC}"
    echo

    COUNT=0
    ERRORS=0

    for yaml_file in examples/skupper-example-*.yaml; do
        if [ -f "$yaml_file" ]; then
            basename="$(basename "$yaml_file" .yaml)"
            echo -n "  Processing $basename... "

            # Generate to individual markdown files
            output_file="examples/${basename}.md"

            if skewer generate "$yaml_file" -o "$output_file" 2>&1 | grep -q "Generated"; then
                echo -e "${GREEN}✓${NC}"
                COUNT=$((COUNT + 1))
            else
                echo -e "${YELLOW}⚠${NC}"
                ERRORS=$((ERRORS + 1))
            fi
        fi
    done

    echo
    echo -e "${GREEN}✓ Generated markdown for $COUNT files${NC}"
    if [ $ERRORS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $ERRORS files had warnings or errors${NC}"
    fi
fi

echo
echo -e "${BLUE}==================================================================${NC}"
echo -e "${GREEN}All operations complete!${NC}"
echo -e "${BLUE}==================================================================${NC}"

# Summary
echo
echo "Summary:"
echo "  - YAML files reformatted with literal block style (|)"
if [ "$GENERATE_MD" = true ]; then
    echo "  - Markdown documentation generated"
fi
echo
echo "Next steps:"
echo "  git status              # Review changes"
echo "  git diff examples/      # See detailed changes"
if [ "$GENERATE_MD" = false ]; then
    echo "  $0 --generate-md        # Generate markdown documentation"
fi
echo
