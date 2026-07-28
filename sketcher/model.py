"""
Phoenix model - Core data model classes.

Parses skewer.yaml files (must be "resolved" - no standard: references).
Much simpler than Skewer since all expansion is done by resolver.py.
"""

import inspect
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple
from urllib.parse import urlparse

from . import utils
from .exceptions import SketcherError


# Load standard text for @default@ substitution
_data_dir = Path(__file__).parent / "data"
_standard_text = utils.read_yaml(_data_dir / "standardtext.yaml")


def object_property(name: str, default: Any = None):
    """
    Property descriptor with @default@ text substitution.

    Simplified version - only handles @default@ replacement in text.
    No site/namespace substitution (resolver handles that).

    Note: Matches Skewer behavior - substitutes @default@ whenever
    value is a string, regardless of whether default is None.
    """
    def get(obj):
        value = obj.data.get(name, default)

        if isinstance(value, str):
            # Replace @default@ with default value
            # Note: Even if default is None, still do replacement
            # This matches original Skewer behavior
            value = value.replace("@default@", str(default or "").strip())
            value = value.strip()

        return value

    return property(get)


def check_required_attributes(obj, *names):
    """Check that object has required attributes."""
    for name in names:
        if name not in obj.data:
            raise SketcherError(f"{obj} is missing required attribute '{name}'")


def check_unknown_attributes(obj):
    """Check for unknown attributes in object data."""
    # Get all property names from the class
    known_attributes = dict(
        inspect.getmembers(obj.__class__, lambda x: isinstance(x, property))
    )

    for name in obj.data:
        if name not in known_attributes:
            raise SketcherError(f"{obj} has unknown attribute '{name}'")


def get_github_owner_repo() -> Tuple[str, str]:
    """
    Extract GitHub owner and repo from git remote origin URL.

    Returns:
        Tuple of (owner, repo)

    Note: Returns tuple (not list) but unpacking works the same:
        owner, repo = get_github_owner_repo()

    Raises:
        SketcherError: If not in a git repo or URL format unknown
    """
    utils.check_program("git")

    url = utils.call("git remote get-url origin", quiet=True)
    result = urlparse(url)

    # SSH format: git@github.com:owner/repo.git
    if result.scheme == "" and result.path.startswith("git@github.com:"):
        path = result.path.removeprefix("git@github.com:")
        path = path.removesuffix(".git")
        parts = path.split("/", 1)
        return (parts[0], parts[1])

    # HTTP(S) format: https://github.com/owner/repo.git
    if result.scheme in ("http", "https") and result.netloc == "github.com":
        path = result.path.removeprefix("/")
        path = path.removesuffix(".git")
        parts = path.split("/", 1)
        return (parts[0], parts[1])

    raise SketcherError(f"Unknown git remote origin URL format: {url}")


def apply_kubeconfigs(model, kubeconfigs: List[str]):
    """
    Apply kubeconfig paths to Kubernetes sites only.

    Args:
        model: Model instance
        kubeconfigs: List of kubeconfig file paths (one per kubernetes site)

    Note: Matches Skewer behavior - only applies to kubernetes sites,
    not podman sites. This allows mixed-platform scenarios.
    """
    if not kubeconfigs:
        return

    # Only get kubernetes sites (matches Skewer behavior)
    kube_sites = [(name, site) for name, site in model.sites if site.platform == "kubernetes"]

    if len(kubeconfigs) < len(kube_sites):
        raise SketcherError(
            f"The provided kubeconfigs are fewer than the number of Kubernetes sites "
            f"({len(kubeconfigs)} kubeconfigs, {len(kube_sites)} kubernetes sites)"
        )

    for (site_name, site), kubeconfig in zip(kube_sites, kubeconfigs):
        site_data = model.data["sites"][site_name]

        if "env" not in site_data:
            site_data["env"] = {}

        site_data["env"]["KUBECONFIG"] = utils.absolute_path(kubeconfig)


class Model:
    """
    Top-level model for a skewer.yaml file.

    Parses yaml and provides access to sites and steps.
    NO standard steps expansion (use resolver.py first).
    """

    # Text properties with @default@ support from standardtext.yaml
    title = object_property("title")
    subtitle = object_property("subtitle")
    workflow = object_property("workflow", "main.yaml")
    overview = object_property("overview")
    prerequisites = object_property("prerequisites", _standard_text.get("prerequisites"))
    summary = object_property("summary")
    next_steps = object_property("next_steps", _standard_text.get("next_steps"))
    about_this_example = object_property("about_this_example", _standard_text.get("about_this_example"))

    def __init__(self, yaml_file: str, kubeconfigs: Optional[List[str]] = None):
        """
        Load and parse a skewer.yaml file.

        Args:
            yaml_file: Path to yaml file (must be resolved, no standard: refs)
            kubeconfigs: Optional list of kubeconfig paths (one per site)
        """
        self.yaml_file = yaml_file
        self.data = utils.read_yaml(yaml_file)

        # Apply kubeconfigs if provided
        if kubeconfigs:
            apply_kubeconfigs(self, kubeconfigs)

    def __repr__(self):
        """Match Skewer's repr format for error messages."""
        return f"model '{self.yaml_file}'"

    def check(self):
        """Validate model structure."""
        check_required_attributes(self, "title", "sites", "steps")
        check_unknown_attributes(self)

        for _, site in self.sites:
            site.check()

        for step in self.steps:
            step.check()

    @property
    def sites(self) -> Generator[Tuple[str, 'Site'], None, None]:
        """Iterate over sites as (name, Site) tuples."""
        for name, data in self.data["sites"].items():
            yield name, Site(self, data, name)

    @property
    def steps(self) -> Generator['Step', None, None]:
        """Iterate over steps."""
        for data in self.data["steps"]:
            yield Step(self, data)


class Site:
    """
    A deployment site (Kubernetes cluster or Podman environment).
    """

    platform = object_property("platform")
    namespace = object_property("namespace")
    env = object_property("env", dict())

    def __init__(self, model: Model, data: Dict[str, Any], name: str):
        """
        Create a Site.

        Args:
            model: Parent Model
            data: Site data from yaml
            name: Site name (key in sites dict)
        """
        assert name is not None

        self.model = model
        self.data = data
        self.name = name

    def __repr__(self):
        """Match Skewer's repr format for error messages."""
        return f"site '{self.name}'"

    def __enter__(self):
        """Context manager: set up logging prefix and environment."""
        self._logging_context = utils.logging_prefix(self.name)
        self._working_env = utils.working_env(**self.env)

        self._logging_context.__enter__()
        self._working_env.__enter__()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager: restore environment and logging."""
        self._working_env.__exit__(exc_type, exc_value, traceback)
        self._logging_context.__exit__(exc_type, exc_value, traceback)

    def check(self):
        """Validate site configuration."""
        check_required_attributes(self, "platform")
        check_unknown_attributes(self)

        if self.platform not in ("kubernetes", "podman", None):
            raise SketcherError(
                f"{self} attribute 'platform' has illegal value: {self.platform}"
            )

        if self.platform == "kubernetes":
            check_required_attributes(self, "namespace")

            if "KUBECONFIG" not in self.env:
                raise SketcherError(
                    f"Kubernetes {self} has no KUBECONFIG environment variable"
                )

        if self.platform == "podman":
            if "SKUPPER_PLATFORM" not in self.env:
                raise SketcherError(
                    f"Podman {self} has no SKUPPER_PLATFORM environment variable"
                )

            platform_value = self.env["SKUPPER_PLATFORM"]

            # Accept podman, docker, or linux (all use same static link mechanism)
            if platform_value not in ("podman", "docker", "linux"):
                raise SketcherError(
                    f"Podman {self} environment variable SKUPPER_PLATFORM "
                    f"has illegal value: {platform_value}. "
                    f"Must be one of: podman, docker, linux"
                )

    @property
    def title(self) -> str:
        """
        Get site title (or capitalized name if not specified).

        Uses utils.capitalize() which only uppercases first char,
        preserving case of rest (unlike Python's str.capitalize()).
        """
        return self.data.get("title", utils.capitalize(self.name))


class Step:
    """
    A step in the workflow.
    """

    numbered = object_property("numbered", True)
    name = object_property("name")
    title = object_property("title")
    preamble = object_property("preamble")
    postamble = object_property("postamble")

    def __init__(self, model: Model, data: Dict[str, Any]):
        """
        Create a Step.

        Args:
            model: Parent Model
            data: Step data from yaml
        """
        self.model = model
        self.data = data

    def __repr__(self):
        """Match Skewer's repr format for error messages."""
        return f"step {self.number} '{self.title}'"

    def check(self):
        """Validate step configuration."""
        check_required_attributes(self, "title")
        check_unknown_attributes(self)

        site_names = [name for name, _ in self.model.sites]

        for site_name, commands in self.commands:
            if site_name not in site_names:
                raise SketcherError(
                    f"Unknown site name '{site_name}' in commands for {self}"
                )

            for command in commands:
                command.check()

    @property
    def number(self) -> int:
        """Get step number (1-indexed)."""
        return self.model.data["steps"].index(self.data) + 1

    @property
    def commands(self) -> Generator[Tuple[str, List['Command']], None, None]:
        """Iterate over commands as (site_name, [Command]) tuples."""
        for site_name, command_data_list in self.data.get("commands", {}).items():
            commands = [Command(self.model, data) for data in command_data_list]
            yield site_name, commands


class Command:
    """
    A command to execute on a site.
    """

    run = object_property("run")
    expect_failure = object_property("expect_failure", False)
    apply = object_property("apply")
    output = object_property("output")
    await_resource = object_property("await_resource")
    await_ingress = object_property("await_ingress")
    await_http_ok = object_property("await_http_ok")
    await_console_ok = object_property("await_console_ok")
    await_port = object_property("await_port")

    def __init__(self, model: Model, data: Dict[str, Any]):
        """
        Create a Command.

        Args:
            model: Parent Model
            data: Command data from yaml
        """
        self.model = model
        self.data = data

    def __repr__(self):
        """Match Skewer's repr format for error messages."""
        if self.run:
            first_line = self.run.splitlines()[0]
            return f"command '{first_line}'"
        return "command"

    def check(self):
        """Validate command configuration."""
        check_unknown_attributes(self)
