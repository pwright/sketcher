"""Kind integration for Phoenix."""

import json
import os
import tempfile
from pathlib import Path
from typing import List

from sketcher import utils, kubernetes
from sketcher.model import Model
from sketcher.exceptions import SketcherError


class Kind:
    """Context manager for Kind-based testing.

    Creates a Kind cluster named 'skewer', and generates kubeconfig files
    for each kubernetes site. Uses NodePort ingress instead of LoadBalancer.

    Example:
        with Kind("skewer.yaml") as k:
            executor.run_steps("skewer.yaml", kubeconfigs=k.kubeconfigs)
    """

    def __init__(self, yaml_file: str):
        """Initialize Kind context manager.

        Args:
            yaml_file: Path to skewer.yaml file
        """
        self.yaml_file = yaml_file
        self.kubeconfigs: List[str] = []
        self.work_dir = Path(tempfile.gettempdir()) / "phoenix"
        self.cluster_name = "skewer"

    def __enter__(self):
        """Start Kind and create kubeconfigs.

        Returns:
            self

        Raises:
            SketcherError: If Kind setup fails
        """
        print("Starting Kind")

        # Check environment
        kubernetes.check_environment()
        utils.check_program("kind")

        # Check for existing 'skewer' cluster
        result = utils.run("kind get clusters", check=False, quiet=True)
        existing_clusters = result.stdout.strip().split("\n") if result.stdout else []

        if self.cluster_name in existing_clusters:
            raise SketcherError(
                f"A Kind cluster '{self.cluster_name}' already exists. "
                f"Delete it using 'kind delete cluster --name {self.cluster_name}'."
            )

        # Create work directory
        if self.work_dir.exists():
            import shutil
            shutil.rmtree(self.work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Create Kind config with NodePort support
        kind_config = self.work_dir / "kind-config.yaml"
        utils.write(kind_config, """
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 8080
    protocol: TCP
  - containerPort: 30443
    hostPort: 8443
    protocol: TCP
  - containerPort: 30010
    hostPort: 8010
    protocol: TCP
""".strip())

        # Create Kind cluster
        utils.run(f"kind create cluster --name {self.cluster_name} --config {kind_config}")

        try:
            # Load model to get sites
            model = Model(self.yaml_file)
            model.check()

            # Generate kubeconfigs for kubernetes sites
            kube_sites = [site for _, site in model.sites if site.platform == "kubernetes"]

            # Get Kind kubeconfig
            base_kubeconfig = utils.call(f"kind get kubeconfig --name {self.cluster_name}", quiet=True)

            for site in kube_sites:
                kubeconfig_path = site.env["KUBECONFIG"]
                kubeconfig_path = kubeconfig_path.replace("~", str(self.work_dir))
                kubeconfig_path = os.path.expanduser(kubeconfig_path)

                # Create kubeconfig directory if needed
                Path(kubeconfig_path).parent.mkdir(parents=True, exist_ok=True)

                # Write kubeconfig for this site
                utils.write(kubeconfig_path, base_kubeconfig)

                site.env["KUBECONFIG"] = kubeconfig_path
                self.kubeconfigs.append(kubeconfig_path)

                # Verify kubeconfig works
                with site:
                    # Test kubectl access
                    result = utils.run("kubectl cluster-info", check=False, quiet=True)
                    if result.returncode != 0:
                        raise SketcherError(f"Kubeconfig not working for site {site.name}")

        except Exception:
            # Delete Kind cluster on failure
            utils.run(f"kind delete cluster --name {self.cluster_name}", check=False)
            raise

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Stop Kind and clean up."""
        print("Stopping Kind")

        # Delete Kind cluster
        utils.run(f"kind delete cluster --name {self.cluster_name}", check=False)
