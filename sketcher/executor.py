"""Step execution logic for Sketcher."""

import os
import tempfile
from pathlib import Path
from typing import Optional, List

from sketcher import utils, kubernetes
from sketcher.model import Model
from sketcher.exceptions import SketcherError, SketcherProcessError


def run_steps(
    yaml_file: str,
    kubeconfigs: Optional[List[str]] = None,
    work_dir: Optional[str] = None,
    debug: bool = False,
    quiet: bool = False
):
    """Run all steps in a skewer.yaml file.

    Args:
        yaml_file: Path to resolved skewer.yaml
        kubeconfigs: Optional list of kubeconfig paths for sites
        work_dir: Working directory for ~ substitution (default: temp dir)
        debug: If True, print debug output on failure
        quiet: If True, suppress progress messages

    Raises:
        SketcherError: If steps fail
    """
    utils.info("Running steps from {}", yaml_file, quiet=quiet)

    # Check environment
    kubernetes.check_environment()

    # Load model
    if kubeconfigs is None:
        kubeconfigs = []

    model = Model(yaml_file, kubeconfigs)
    model.check()

    # Create work directory
    if work_dir is None:
        work_dir = tempfile.mkdtemp(prefix="sketcher-")
        utils.info("Using work directory: {}", work_dir, quiet=quiet)
    else:
        Path(work_dir).mkdir(parents=True, exist_ok=True)

    try:
        # Run all steps except cleaning_up
        for step in model.steps:
            if step.name == "cleaning_up":
                continue

            run_step(model, step, work_dir, quiet=quiet)

        # Demo mode support
        if "SKETCHER_DEMO" in os.environ:
            from sketcher import demo
            demo.save_demo_context(model, work_dir)
            demo.pause_for_demo(model, quiet=quiet)

    except Exception as e:
        if debug:
            print_debug_output(model)

        raise
    finally:
        # Always run cleaning_up (if it exists)
        for step in model.steps:
            if step.name == "cleaning_up":
                run_step(model, step, work_dir, check=False, quiet=True)
                break


def run_step(model: Model, step, work_dir: str, check: bool = True, quiet: bool = False):
    """Run a single step.

    Args:
        model: Sketcher Model instance
        step: Step to run
        work_dir: Working directory for ~ substitution
        check: If True, raise error on command failure
        quiet: If True, suppress progress messages

    Raises:
        SketcherError: If command fails and check=True
    """
    if not step.commands:
        return

    # Check if all commands are readme-only - if so, skip the entire step
    all_readme = True
    for site_name, commands in step.commands:
        for command in commands:
            if command.apply != "readme":
                all_readme = False
                break
        if not all_readme:
            break

    if all_readme:
        return

    # Use operation context for visual hierarchy
    with utils.operation(str(step), quiet=quiet):
        sites_dict = dict(model.sites)

        for site_name, commands in step.commands:
            site = sites_dict[site_name]

            # Use site context manager (sets env vars and logging prefix)
            with site:
                # Set kubectl namespace for kubernetes sites
                if site.platform == "kubernetes":
                    utils.run(
                        f"kubectl config set-context --current --namespace {site.namespace}",
                        quiet=True,
                        stdout=utils.subprocess.DEVNULL
                    )

                # Execute commands
                for command in commands:
                    # Skip README-only commands
                    if command.apply == "readme":
                        continue

                    # Execute await operations
                    if command.await_resource:
                        utils.debug(f"Awaiting resource: {command.await_resource}")
                        kubernetes.await_resource(command.await_resource, quiet=quiet)

                    if command.await_ingress:
                        utils.debug(f"Awaiting ingress: {command.await_ingress}")
                        kubernetes.await_ingress(command.await_ingress, quiet=quiet)

                    if command.await_http_ok:
                        # await_http_ok is a tuple: (service, url_template, user, password)
                        utils.debug(f"Awaiting HTTP OK: {command.await_http_ok[0]}")
                        kubernetes.await_http_ok(*command.await_http_ok, quiet=quiet)

                    if command.await_console_ok:
                        utils.debug("Awaiting console OK")
                        kubernetes.await_console_ok(quiet=quiet)

                    if command.await_port:
                        utils.debug(f"Awaiting port: {command.await_port}")
                        kubernetes.await_port(command.await_port, quiet=quiet)

                    # Execute shell command
                    if command.run:
                        # Replace ~ with work_dir
                        cmd = command.run.replace("~", work_dir)

                        # Wrap localhost curl commands with retry logic
                        if "curl" in cmd and "localhost" in cmd and "http://" in cmd:
                            # Add retry flags to make curl more resilient
                            # max-time 15 allows for slower app startup, retry-all-errors catches transient failures
                            if "--retry" not in cmd:
                                cmd = cmd.replace("curl ", "curl --retry 20 --retry-delay 3 --retry-all-errors --max-time 15 ")

                        result = utils.run(cmd, shell=True, check=False, quiet=quiet)

                        # Handle expect_failure
                        if command.expect_failure:
                            if result.returncode == 0:
                                raise SketcherError("A command expected to fail did not fail")
                            continue

                        # Check for failure
                        if check and result.returncode != 0:
                            err = SketcherProcessError(
                                f"Command failed in {step}",
                                result.returncode,
                                result.stdout,
                                result.stderr
                            )
                            raise err


def print_debug_output(model: Model):
    """Print debug output for all sites.

    Shows kubectl get all and skupper status for each site.

    Args:
        model: Sketcher Model instance
    """
    utils.eprint("\n" + "=" * 80)
    utils.cprint("DEBUG OUTPUT", color="yellow", file=utils.sys.stderr)
    utils.eprint("=" * 80)

    for site_name, site in model.sites:
        utils.cprint(f"\n--- {site.title} ({site_name}) ---\n", color="cyan", file=utils.sys.stderr)

        with site:
            if site.platform == "kubernetes":
                # Set namespace
                utils.run(
                    f"kubectl config set-context --current --namespace {site.namespace}",
                    quiet=True,
                    stdout=utils.subprocess.DEVNULL,
                    check=False
                )

                # Show all resources
                utils.eprint("kubectl get all:")
                utils.run("kubectl get all", check=False)
                utils.eprint()

            # Show skupper status
            utils.eprint("skupper status:")
            utils.run("skupper status", check=False)
            utils.eprint()

            utils.eprint("skupper link status:")
            utils.run("skupper link status", check=False)
            utils.eprint()

    utils.eprint("=" * 80)
