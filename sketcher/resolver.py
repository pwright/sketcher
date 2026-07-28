"""
Phoenix resolver - Migration tool to expand standard steps.

This module implements the standard step expansion logic from Skewer
as a standalone migration tool. It reads skewer.yaml files with
`standard:` references and expands them to complete yaml files.

One-time use: phoenix resolve input.yaml -o output.yaml
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import utils
from .exceptions import SketcherError


def resolve_yaml_file(input_file: str, output_file: Optional[str] = None) -> str:
    """
    Resolve standard steps in a skewer.yaml file.

    Args:
        input_file: Path to input yaml with standard: references
        output_file: Path to output yaml (or None for stdout)

    Returns:
        Resolved yaml content as string
    """
    utils.notice(f"Resolving {input_file}")

    # Load inputs
    data = utils.read_yaml(input_file)

    # Load standard steps and text
    data_dir = Path(__file__).parent / "data"
    standard_steps = utils.read_yaml(data_dir / "standardsteps.yaml")
    standard_text = utils.read_yaml(data_dir / "standardtext.yaml")

    # Build old_name lookup
    standard_steps_by_old_name = {}
    for name, step_data in standard_steps.items():
        if "old_name" in step_data:
            standard_steps_by_old_name[step_data["old_name"]] = {
                **step_data,
                "new_name": name
            }

    sites = data.get("sites", {})
    resolved_steps = []

    # Process each step
    for step in data.get("steps", []):
        if "standard" in step:
            resolved_step = expand_standard_step(
                step,
                standard_steps,
                standard_steps_by_old_name,
                standard_text,
                sites
            )
            resolved_steps.append(resolved_step)
        else:
            # Keep non-standard steps as-is
            resolved_steps.append(step)

    # Update steps in data
    data["steps"] = resolved_steps

    # Write output
    content = utils.write_yaml_to_string(data)

    if output_file:
        utils.write(output_file, content)
        utils.notice(f"Wrote resolved yaml to {output_file}")
    else:
        print(content)

    return content


def expand_standard_step(
    step: Dict[str, Any],
    standard_steps: Dict[str, Any],
    standard_steps_by_old_name: Dict[str, Any],
    standard_text: Dict[str, Any],
    sites: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Expand a single standard step reference.

    Args:
        step: Step data with "standard" key
        standard_steps: All standard steps
        standard_steps_by_old_name: Old name mappings
        standard_text: Standard text blocks
        sites: Site definitions from yaml

    Returns:
        Expanded step data (without "standard" key)
    """
    standard_step_name = step["standard"]

    # Look up standard step
    try:
        standard_step_data = standard_steps[standard_step_name]
    except KeyError:
        # Try old name
        try:
            standard_step_data = standard_steps_by_old_name[standard_step_name]
            new_name = standard_step_data["new_name"]
            utils.warn(f"Step '{standard_step_name}' has a new name: '{new_name}'")
        except KeyError:
            utils.fail(f"Standard step '{standard_step_name}' not found")

    # Create resolved step (copy user overrides)
    resolved = {k: v for k, v in step.items() if k != "standard"}

    # Apply attributes with @default@ substitution
    def apply_attribute(name: str, default: Any = None):
        standard_value = standard_step_data.get(name, default)
        user_value = step.get(name)

        # User provided value, or use standard
        if user_value is not None:
            value = user_value
        else:
            value = standard_value

        # Apply @default@ substitution if string
        if isinstance(value, str) and standard_value is not None:
            value = value.replace("@default@", str(standard_value or "").strip())

        # Apply @siteN@ and @namespaceN@ substitution
        if isinstance(value, str):
            for i, (site_name, site_data) in enumerate(sites.items()):
                site_title = site_data.get("title", site_name)
                value = value.replace(f"@site{i}@", site_title)

                if "namespace" in site_data:
                    value = value.replace(f"@namespace{i}@", site_data["namespace"])

            value = value.strip()

        if value is not None:
            resolved[name] = value

    # Apply standard attributes
    apply_attribute("name")
    apply_attribute("title")
    apply_attribute("numbered", True)
    apply_attribute("preamble")
    apply_attribute("postamble")

    # Handle commands
    platform = standard_step_data.get("platform")

    if "commands" not in step and "commands" in standard_step_data:
        resolved["commands"] = {}

        for i, (site_name, site_data) in enumerate(sites.items()):
            # Skip if platform doesn't match
            if platform and site_data.get("platform") != platform:
                continue

            # Check for index-specific commands first, then wildcard
            standard_commands = standard_step_data["commands"]

            if str(i) in standard_commands:
                # Specific index
                commands = standard_commands[str(i)]
            elif "*" in standard_commands:
                # Wildcard
                commands = standard_commands["*"]
            else:
                # No commands for this site
                continue

            # Resolve command variables
            resolved["commands"][site_name] = resolve_command_variables(
                commands,
                site_name,
                site_data
            )

    return resolved


def resolve_command_variables(
    commands: List[Dict[str, Any]],
    site_name: str,
    site_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Resolve @kubeconfig@ and @namespace@ in commands.

    Args:
        commands: List of command dicts
        site_name: Name of the site
        site_data: Site configuration data

    Returns:
        List of resolved commands
    """
    resolved_commands = []

    platform = site_data.get("platform")
    namespace = site_data.get("namespace", "")
    kubeconfig = site_data.get("env", {}).get("KUBECONFIG", "")

    for command in commands:
        resolved_command = dict(command)

        # Resolve variables in "run" field
        if "run" in command:
            resolved_command["run"] = command["run"]

            if platform == "kubernetes":
                resolved_command["run"] = resolved_command["run"].replace(
                    "@kubeconfig@", kubeconfig
                )
                resolved_command["run"] = resolved_command["run"].replace(
                    "@namespace@", namespace
                )

        # Resolve variables in "output" field
        if "output" in command:
            resolved_command["output"] = command["output"]

            if platform == "kubernetes":
                resolved_command["output"] = resolved_command["output"].replace(
                    "@kubeconfig@", kubeconfig
                )
                resolved_command["output"] = resolved_command["output"].replace(
                    "@namespace@", namespace
                )

        resolved_commands.append(resolved_command)

    return resolved_commands


def resolve_file_in_place(file_path: str):
    """
    Resolve standard steps in a file in-place.

    Args:
        file_path: Path to yaml file to resolve
    """
    content = resolve_yaml_file(file_path, output_file=None)
    utils.write(file_path, content)
    utils.notice(f"Resolved {file_path} in-place")


def main():
    """CLI entry point for resolver."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Expand standard steps in skewer.yaml files"
    )
    parser.add_argument("input_file", help="Input yaml file with standard: references")
    parser.add_argument(
        "-o", "--output",
        help="Output file (default: print to stdout)"
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Modify input file in-place"
    )

    args = parser.parse_args()

    try:
        if args.in_place:
            if args.output:
                utils.fail("Cannot use both --in-place and --output")
            resolve_file_in_place(args.input_file)
        else:
            resolve_yaml_file(args.input_file, args.output)
    except SketcherError as e:
        utils.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
