"""Demo mode functionality for Phoenix."""

import json
import os
import signal
import time
from pathlib import Path
from typing import Optional, Dict, Any

from sketcher import utils, kubernetes
from sketcher.model import Model
from sketcher.exceptions import SketcherError


def save_demo_context(model: Model, work_dir: str):
    """Save current demo context to JSON state file.

    This allows another process to attach to the running demo
    and execute additional steps in the same environment.

    Args:
        model: Phoenix Model instance
        work_dir: Working directory path
    """
    context_file = Path(work_dir) / ".demo-context.json"

    # Extract site data from model
    sites_data = {}
    for site_name, site in model.sites:
        site_data = {
            "platform": site.platform,
            "env": dict(site.env)
        }
        if site.namespace:
            site_data["namespace"] = site.namespace
        if "title" in site.data:
            site_data["title"] = site.data["title"]
        sites_data[site_name] = site_data

    context = {
        "version": "1.0",
        "created_at": time.time(),
        "pid": os.getpid(),
        "work_dir": work_dir,
        "yaml_file": model.yaml_file,
        "sites": sites_data,
        "demo_active": True
    }

    utils.write_json(context_file, context)
    utils.info("Demo context saved (PID {})", context['pid'])


def load_demo_context(work_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Load demo context from state file if it exists.

    Args:
        work_dir: Working directory (default: $TMPDIR/phoenix)

    Returns:
        Demo context dict or None if no demo is running
    """
    if work_dir is None:
        work_dir = Path("/tmp") / "phoenix"

    context_file = Path(work_dir) / ".demo-context.json"

    if not context_file.exists():
        return None

    try:
        return utils.read_json(context_file)
    except Exception:
        return None


def is_demo_active(context: Dict[str, Any]) -> bool:
    """Check if the demo process is still running.

    Args:
        context: Demo context dict

    Returns:
        True if the process exists and is alive
    """
    pid = context.get("pid")
    if not pid:
        return False

    try:
        # Signal 0 checks process existence without killing it
        os.kill(pid, 0)
        return context.get("demo_active", False)
    except (OSError, ProcessLookupError):
        return False


def validate_demo_context(context: Optional[Dict[str, Any]]):
    """Validate that demo context is usable.

    Args:
        context: Demo context dict

    Raises:
        SketcherError: If validation fails with helpful message
    """
    if not context:
        raise SketcherError("No active demo found. Run 'phoenix demo' first in another terminal.")

    if not is_demo_active(context):
        pid = context.get("pid", "unknown")
        raise SketcherError(
            f"Demo process (PID {pid}) is no longer running. Please restart the demo."
        )

    work_dir = context.get("work_dir")
    if not work_dir or not Path(work_dir).is_dir():
        raise SketcherError("Demo work directory not found. Demo may have been cleaned up.")

    # Validate kubeconfigs exist
    for site_name, site_data in context.get("sites", {}).items():
        if site_data.get("platform") == "kubernetes":
            kubeconfig = site_data.get("env", {}).get("KUBECONFIG")
            if kubeconfig and not Path(kubeconfig).exists():
                raise SketcherError(f"Kubeconfig for site '{site_name}' not found: {kubeconfig}")


def create_extended_model(context: Dict[str, Any], extend_file: str) -> Model:
    """Create a Model instance from saved context + extend file.

    This reconstructs the site configuration from the saved context
    and applies the steps from the extend file.

    Args:
        context: Demo context dict
        extend_file: Path to extension yaml file

    Returns:
        Model instance with extended steps

    Raises:
        SketcherError: If extend file is invalid
    """
    extend_path = Path(extend_file)

    # Read and validate extend file
    if not extend_path.exists():
        raise SketcherError(f"Extend file not found: {extend_file}")

    extend_data = utils.read_yaml(extend_path)

    if not isinstance(extend_data, dict):
        raise SketcherError("Invalid extend file format: expected YAML dictionary")

    if "steps" not in extend_data:
        raise SketcherError(f"Extend file '{extend_file}' must contain a 'steps' section")

    if not isinstance(extend_data["steps"], list):
        raise SketcherError("'steps' section must be a list of step definitions")

    # Clean up site data
    sites_data = {}
    for site_name, site_data in context["sites"].items():
        clean_site_data = dict(site_data)
        # Remove 'name' if present (it's passed separately to Site constructor)
        clean_site_data.pop("name", None)
        sites_data[site_name] = clean_site_data

    # Build a synthetic skewer.yaml structure
    synthetic_data = {
        "title": f"Extended Demo from {extend_file}",
        "sites": sites_data,
        "steps": extend_data["steps"]
    }

    # Write synthetic file temporarily
    work_dir = context["work_dir"]
    synthetic_file = Path(work_dir) / ".extended-model.yaml"
    utils.write_yaml(synthetic_file, synthetic_data)

    # Create model
    model = Model(str(synthetic_file), kubeconfigs=[])

    # Override site env vars from context (already expanded paths)
    for site_name, site in model.sites:
        if site_name in context["sites"]:
            site.env.update(context["sites"][site_name]["env"])

    model.check()
    return model


def pause_for_demo(model: Model, quiet: bool = False):
    """Pause for interactive demo time.

    Shows console URLs, frontend URLs, and waits for user input.

    Args:
        model: Phoenix Model instance
        quiet: If True, suppress progress messages
    """
    utils.notice("Pausing for demo time", quiet=quiet)

    first_site = list(model.sites)[0][1]
    console_url = None
    password = None
    frontend_url = None

    # Check for frontend and console (kubernetes only)
    if first_site.platform == "kubernetes":
        with first_site:
            if kubernetes.resource_exists("deployment/frontend"):
                frontend_url = "http://localhost:8080/"

            if kubernetes.resource_exists("secret/skupper-console-users"):
                console_host = kubernetes.await_ingress("service/skupper")
                console_url = f"https://{console_host}:8010/"

                kubernetes.await_resource("secret/skupper-console-users")
                password = kubernetes.get_resource_json("secret/skupper-console-users", ".data.admin")
                password = utils.base64_decode(password)

    utils.eprint()
    utils.cprint("Demo time!", color="cyan", file=utils.sys.stderr)
    utils.eprint()
    utils.cprint("Sites:", color="cyan", file=utils.sys.stderr)
    utils.eprint()

    for site_name, site in model.sites:
        if site.platform == "kubernetes":
            kubeconfig = site.env["KUBECONFIG"]
            utils.eprint(f"  {site_name}: export KUBECONFIG={kubeconfig}")
        elif site.platform == "podman":
            utils.eprint(f"  {site_name}: export SKUPPER_PLATFORM=podman")

    utils.eprint()

    if frontend_url:
        utils.cprint(f"Frontend URL:     {frontend_url}", color="green", file=utils.sys.stderr)
        utils.eprint()

    if console_url:
        utils.cprint(f"Console URL:      {console_url}", color="green", file=utils.sys.stderr)
        utils.eprint("Console user:     admin")
        utils.cprint(f"Console password: {password}", color="yellow", file=utils.sys.stderr)
        utils.eprint()

    # Wait for user (unless PHOENIX_DEMO_NO_WAIT is set)
    if "PHOENIX_DEMO_NO_WAIT" not in os.environ:
        while input("Are you done (yes)? ") != "yes":
            pass
