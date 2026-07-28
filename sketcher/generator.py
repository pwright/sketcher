"""README generation from resolved Phoenix yaml files."""

import re
from pathlib import Path
from typing import Optional

from sketcher import utils
from sketcher.model import Model


def generate_readme(yaml_file: str, output_file: Optional[str] = None, quiet: bool = False) -> str:
    """Generate README.md from a resolved Phoenix yaml file.

    Args:
        yaml_file: Path to resolved skewer.yaml file
        output_file: Output path (default: README.md in same directory as yaml_file)
        quiet: If True, suppress progress messages

    Returns:
        Path to generated README file
    """
    yaml_path = Path(yaml_file).resolve()

    if output_file is None:
        output_file = yaml_path.parent / "README.md"
    else:
        output_file = Path(output_file)

    utils.info("Generating README from {}", yaml_path, quiet=quiet)

    model = Model(str(yaml_path))
    model.check()

    # Load standard text
    standard_text_file = Path(__file__).parent / "data" / "standardtext.yaml"
    standard_text = utils.read_yaml(standard_text_file)

    lines = []

    def append_toc_entry(heading: str, condition: bool = True):
        """Add a table of contents entry."""
        if not condition:
            return

        # Convert heading to GitHub anchor fragment
        fragment = re.sub(r"[ -]", "_", heading)
        fragment = re.sub(r"[\W]", "", fragment)
        fragment = fragment.replace("_", "-")
        fragment = fragment.lower()

        lines.append(f"* [{heading}](#{fragment})")

    def append_section(heading: str, text: Optional[str]):
        """Add a section with heading and content."""
        if not text:
            return

        lines.append(f"## {heading}")
        lines.append("")
        lines.append(text)
        lines.append("")

    def generate_step_heading(step) -> str:
        """Generate heading for a step."""
        if step.numbered:
            return f"Step {step.number}: {step.title}"
        else:
            return step.title

    def generate_workflow_url(workflow: str) -> Optional[str]:
        """Generate GitHub Actions workflow URL.

        Returns None if git origin is not a GitHub URL.
        """
        # If workflow is already a URL, return it
        if "://" in workflow:
            return workflow

        # Otherwise, construct GitHub Actions URL
        try:
            owner, repo = utils.get_github_owner_repo()
            return f"https://github.com/{owner}/{repo}/actions/workflows/{workflow}"
        except Exception:
            # Not a GitHub repo or no git origin
            return None

    # Header comment
    lines.append("<!-- NOTE: This file is generated from skewer.yaml.  Do not edit it directly. -->")
    lines.append("")

    # Title
    lines.append(f"# {model.title}")
    lines.append("")

    # Workflow badge (if defined and git origin is GitHub)
    if model.workflow:
        url = generate_workflow_url(model.workflow)
        if url:
            lines.append(f"[![main]({url}/badge.svg)]({url})")
            lines.append("")

    # Subtitle
    if model.subtitle:
        lines.append(f"#### {model.subtitle}")
        lines.append("")

    # Example suite blurb
    lines.append(standard_text["example_suite"].strip())
    lines.append("")

    # Table of Contents
    lines.append("#### Contents")
    lines.append("")

    append_toc_entry("Overview", bool(model.overview))
    append_toc_entry("Prerequisites", bool(model.prerequisites))
    append_toc_entry("Sites")

    for step in model.steps:
        append_toc_entry(generate_step_heading(step))

    append_toc_entry("Summary", bool(model.summary))
    append_toc_entry("Next steps", bool(model.next_steps))
    append_toc_entry("About this example", bool(model.about_this_example))

    lines.append("")

    # Sections
    append_section("Overview", model.overview)
    append_section("Prerequisites", model.prerequisites)

    # Sites section
    sites_text = generate_sites_section(model)
    append_section("Sites", sites_text)

    # Steps
    for step in model.steps:
        heading = generate_step_heading(step)
        text = generate_readme_step(model, step)
        append_section(heading, text)

    append_section("Summary", model.summary)
    append_section("Next steps", model.next_steps)
    append_section("About this example", model.about_this_example)

    # Write output
    content = "\n".join(lines).strip() + "\n"
    utils.write(output_file, content)

    utils.cprint(f"Generated {output_file} ({len(content)} bytes)", color="green")
    return str(output_file)


def generate_sites_section(model: Model) -> str:
    """Generate markdown for the Sites section.

    Shows the platform, namespace, and environment setup for each site.

    Args:
        model: Phoenix Model instance

    Returns:
        Markdown text for the sites section
    """
    lines = []

    lines.append("This example uses the following sites:")
    lines.append("")

    for site_name, site in model.sites:
        lines.append(f"_**{site.title}:**_")
        lines.append("")

        if site.platform == "kubernetes":
            lines.append("~~~ shell")
            lines.append(f"export KUBECONFIG=~/.kube/config-{site_name}")
            lines.append(f"kubectl config set-context --current --namespace {site.namespace}")
            lines.append("~~~")
        elif site.platform == "podman":
            lines.append("~~~ shell")
            lines.append("export SKUPPER_PLATFORM=podman")
            lines.append("~~~")

        lines.append("")

    return "\n".join(lines).strip()


def generate_readme_step(model: Model, step) -> str:
    """Generate markdown for a single step.

    Args:
        model: Phoenix Model instance
        step: Step to generate markdown for

    Returns:
        Markdown text for the step
    """
    lines = []

    # Preamble
    if step.preamble:
        lines.append(step.preamble.strip())
        lines.append("")

    # Commands for each site
    sites_dict = dict(model.sites)

    for site_name, commands in step.commands:
        site = sites_dict[site_name]
        outputs = []

        # Site heading
        lines.append(f"_**{site.title}:**_")
        lines.append("")
        lines.append("~~~ shell")

        # Commands
        for command in commands:
            # Skip test-only commands
            if command.apply == "test":
                continue

            if command.run:
                lines.append(command.run)

            # Save output for later
            if command.output:
                assert command.run
                outputs.append((command.run, command.output))

        lines.append("~~~")
        lines.append("")

        # Sample output section
        if outputs:
            lines.append("_Sample output:_")
            lines.append("")
            lines.append("~~~ console")

            # Format: $ command\noutput
            output_blocks = []
            for run, output in outputs:
                output_blocks.append(f"$ {run}\n{output.strip()}")

            lines.append("\n\n".join(output_blocks))
            lines.append("~~~")
            lines.append("")

    # Postamble
    if step.postamble:
        lines.append(step.postamble.strip())

    return "\n".join(lines).strip()


def generate_extend_readme(extend_file: str, output_file: Optional[str] = None) -> str:
    """Generate README for extension yaml files.

    Extension files (skewer-extend-*.yaml) have simpler structure:
    - No overview/prerequisites/summary
    - Just title and steps

    Args:
        extend_file: Path to extension yaml file
        output_file: Output path (default: same name as extend_file but .md)

    Returns:
        Path to generated README file
    """
    extend_path = Path(extend_file).resolve()

    if output_file is None:
        output_file = extend_path.with_suffix(".md")
    else:
        output_file = Path(output_file)

    utils.info("Generating extension README from {}", extend_path)

    model = Model(str(extend_path))
    model.check()

    lines = []

    # Header comment
    lines.append(f"<!-- NOTE: This file is generated from {extend_path.name}.  Do not edit it directly. -->")
    lines.append("")

    # Title
    lines.append(f"# {model.title}")
    lines.append("")

    # Steps (no TOC for extension files)
    for step in model.steps:
        heading = step.title  # Extension steps are not numbered
        text = generate_readme_step(model, step)

        lines.append(f"## {heading}")
        lines.append("")
        lines.append(text)
        lines.append("")

    # Write output
    content = "\n".join(lines).strip() + "\n"
    utils.write(output_file, content)

    utils.cprint(f"Generated {output_file} ({len(content)} bytes)", color="green")
    return str(output_file)
