"""Minikube integration for Phoenix."""

import json
import os
import tempfile
from pathlib import Path
from typing import List

from sketcher import utils, kubernetes
from sketcher.model import Model
from sketcher.exceptions import SketcherError


class Minikube:
    """Context manager for Minikube-based testing.

    Creates a Minikube profile named 'skewer', starts a tunnel,
    and generates kubeconfig files for each kubernetes site.

    Example:
        with Minikube("skewer.yaml") as mk:
            executor.run_steps("skewer.yaml", kubeconfigs=mk.kubeconfigs)
    """

    def __init__(self, yaml_file: str):
        """Initialize Minikube context manager.

        Args:
            yaml_file: Path to skewer.yaml file
        """
        self.yaml_file = yaml_file
        self.kubeconfigs: List[str] = []
        self.work_dir = Path(tempfile.gettempdir()) / "phoenix"
        self.tunnel_process = None

    def __enter__(self):
        """Start Minikube and create kubeconfigs.

        Returns:
            self

        Raises:
            SketcherError: If Minikube setup fails
        """
        print("Starting Minikube")

        # Check environment
        kubernetes.check_environment()
        utils.check_program("minikube")

        # Check for existing 'skewer' profile
        profile_data = json.loads(utils.call("minikube profile list --output json", quiet=True))

        for profile in profile_data.get("valid", []):
            if profile["Name"] == "skewer":
                raise SketcherError(
                    "A Minikube profile 'skewer' already exists. "
                    "Delete it using 'minikube delete -p skewer'."
                )

        # Create work directory
        if self.work_dir.exists():
            import shutil
            shutil.rmtree(self.work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Start Minikube
        utils.run("minikube start -p skewer --auto-update-drivers false")

        try:
            # Start tunnel (background)
            tunnel_output_path = str(self.work_dir / "minikube-tunnel-output")
            self.tunnel_process = utils.start_process(
                "minikube tunnel -p skewer",
                stdout_file=tunnel_output_path,
                stderr_file=tunnel_output_path
            )

            try:
                # Load model to get sites
                model = Model(self.yaml_file)
                model.check()

                # Generate kubeconfigs for kubernetes sites
                kube_sites = [site for _, site in model.sites if site.platform == "kubernetes"]

                for site in kube_sites:
                    kubeconfig = site.env["KUBECONFIG"]
                    kubeconfig = kubeconfig.replace("~", str(self.work_dir))
                    kubeconfig = os.path.expanduser(kubeconfig)

                    site.env["KUBECONFIG"] = kubeconfig
                    self.kubeconfigs.append(kubeconfig)

                    with site:
                        utils.run("minikube update-context -p skewer")

                        # Verify kubeconfig was created
                        if not Path(os.environ["KUBECONFIG"]).exists():
                            raise SketcherError(f"Kubeconfig not created: {os.environ['KUBECONFIG']}")

            except Exception:
                # Stop tunnel on failure
                if self.tunnel_process:
                    utils.stop_process(self.tunnel_process)
                raise

        except Exception:
            # Delete Minikube profile on failure
            utils.run("minikube delete -p skewer", check=False)
            raise

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Stop Minikube and clean up."""
        print("Stopping Minikube")

        # Stop tunnel
        if self.tunnel_process:
            utils.stop_process(self.tunnel_process)

        # Delete Minikube profile
        utils.run("minikube delete -p skewer", check=False)
