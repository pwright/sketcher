"""
Unit tests for phoenix.resolver module.
"""

import tempfile
import unittest
from pathlib import Path

from sketcher import resolver, utils


class TestResolver(unittest.TestCase):
    """Test resolver functions."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_resolve_yaml_file(self):
        """Test resolving a complete yaml file."""
        input_file = self.fixtures_dir / "skewer.yaml"
        output_file = Path(self.temp_dir) / "resolved.yaml"

        # Resolve the file
        resolver.resolve_yaml_file(str(input_file), str(output_file))

        # Verify output exists
        self.assertTrue(output_file.exists())

        # Load and verify resolved yaml
        resolved = utils.read_yaml(output_file)

        # Should have same title and sites
        self.assertEqual(resolved["title"], "Skupper Hello World")
        self.assertIn("west", resolved["sites"])
        self.assertIn("east", resolved["sites"])

        # Should have steps
        self.assertGreater(len(resolved["steps"]), 0)

        # Steps should not have "standard" key anymore
        for step in resolved["steps"]:
            self.assertNotIn("standard", step)
            # Should have title
            self.assertIn("title", step)

    def test_expand_standard_step(self):
        """Test expanding a single standard step."""
        data_dir = Path(__file__).parent.parent / "sketcher" / "data"
        standard_steps = utils.read_yaml(data_dir / "standardsteps.yaml")
        standard_text = utils.read_yaml(data_dir / "standardtext.yaml")

        sites = {
            "west": {
                "title": "West",
                "platform": "kubernetes",
                "namespace": "west",
                "env": {"KUBECONFIG": "~/.kube/config-west"}
            },
            "east": {
                "title": "East",
                "platform": "kubernetes",
                "namespace": "east",
                "env": {"KUBECONFIG": "~/.kube/config-east"}
            }
        }

        step = {"standard": "platform/create_your_kubernetes_namespaces"}

        # Build old_name lookup
        standard_steps_by_old_name = {}
        for name, step_data in standard_steps.items():
            if "old_name" in step_data:
                standard_steps_by_old_name[step_data["old_name"]] = {
                    **step_data,
                    "new_name": name
                }

        resolved = resolver.expand_standard_step(
            step,
            standard_steps,
            standard_steps_by_old_name,
            standard_text,
            sites
        )

        # Should have title
        self.assertIn("title", resolved)

        # Should have commands for both sites
        self.assertIn("commands", resolved)
        self.assertIn("west", resolved["commands"])
        self.assertIn("east", resolved["commands"])

        # Should not have "standard" key
        self.assertNotIn("standard", resolved)

    def test_resolve_command_variables(self):
        """Test command variable resolution."""
        site_data = {
            "platform": "kubernetes",
            "namespace": "test-ns",
            "env": {"KUBECONFIG": "~/.kube/config-test"}
        }

        commands = [
            {
                "run": "export KUBECONFIG=@kubeconfig@"
            },
            {
                "run": "kubectl create namespace @namespace@",
                "output": "namespace/@namespace@ created"
            }
        ]

        resolved = resolver.resolve_command_variables(
            commands,
            "test",
            site_data
        )

        self.assertEqual(len(resolved), 2)
        self.assertEqual(
            resolved[0]["run"],
            "export KUBECONFIG=~/.kube/config-test"
        )
        self.assertEqual(
            resolved[1]["run"],
            "kubectl create namespace test-ns"
        )
        self.assertEqual(
            resolved[1]["output"],
            "namespace/test-ns created"
        )

    def test_resolve_with_index_commands(self):
        """Test resolving steps with indexed commands (0, 1, *)."""
        data_dir = Path(__file__).parent.parent / "sketcher" / "data"
        standard_steps = utils.read_yaml(data_dir / "standardsteps.yaml")
        standard_text = utils.read_yaml(data_dir / "standardtext.yaml")

        sites = {
            "west": {
                "title": "West",
                "platform": "kubernetes",
                "namespace": "west",
                "env": {"KUBECONFIG": "~/.kube/config-west"}
            },
            "east": {
                "title": "East",
                "platform": "kubernetes",
                "namespace": "east",
                "env": {"KUBECONFIG": "~/.kube/config-east"}
            }
        }

        # This standard step has different commands for site 0 vs *
        step = {"standard": "skupper/create_your_sites/kubernetes_cli"}

        standard_steps_by_old_name = {}

        resolved = resolver.expand_standard_step(
            step,
            standard_steps,
            standard_steps_by_old_name,
            standard_text,
            sites
        )

        # Both sites should have commands
        self.assertIn("west", resolved["commands"])
        self.assertIn("east", resolved["commands"])

        # Site 0 (west) should have --enable-link-access
        west_run = resolved["commands"]["west"][0]["run"]
        self.assertIn("--enable-link-access", west_run)

        # Site 1 (east) should NOT have --enable-link-access (uses wildcard)
        east_run = resolved["commands"]["east"][0]["run"]
        self.assertNotIn("--enable-link-access", east_run)

    def test_resolve_with_default_merging(self):
        """Test @default@ merging in user-provided content."""
        data_dir = Path(__file__).parent.parent / "sketcher" / "data"
        standard_steps = utils.read_yaml(data_dir / "standardsteps.yaml")
        standard_text = utils.read_yaml(data_dir / "standardtext.yaml")

        sites = {
            "west": {
                "platform": "kubernetes",
                "namespace": "west"
            }
        }

        # User provides preamble with @default@
        step = {
            "standard": "hello_world/cleaning_up/kubernetes_cli",
            "preamble": "@default@\n\nAnd more custom text!"
        }

        standard_steps_by_old_name = {}

        resolved = resolver.expand_standard_step(
            step,
            standard_steps,
            standard_steps_by_old_name,
            standard_text,
            sites
        )

        # Preamble should have standard text + custom text
        self.assertIn("preamble", resolved)
        preamble = resolved["preamble"]
        self.assertIn("And more custom text!", preamble)
        # Should also have the standard preamble content
        self.assertGreater(len(preamble), len("And more custom text!"))

    def test_resolve_in_place(self):
        """Test in-place resolution."""
        # Create a temp input file
        input_file = Path(self.temp_dir) / "test.yaml"

        # Simple yaml with standard step
        test_yaml = {
            "title": "Test",
            "sites": {
                "test": {
                    "platform": "kubernetes",
                    "namespace": "test"
                }
            },
            "steps": [
                {"standard": "platform/create_your_kubernetes_namespaces"}
            ]
        }

        utils.write_yaml(input_file, test_yaml)

        # Resolve in-place
        resolver.resolve_file_in_place(str(input_file))

        # Load and verify
        resolved = utils.read_yaml(input_file)
        self.assertNotIn("standard", resolved["steps"][0])
        self.assertIn("title", resolved["steps"][0])

    def test_platform_filtering(self):
        """Test that platform-specific steps are filtered correctly."""
        data_dir = Path(__file__).parent.parent / "sketcher" / "data"
        standard_steps = utils.read_yaml(data_dir / "standardsteps.yaml")
        standard_text = utils.read_yaml(data_dir / "standardtext.yaml")

        # Mix of kubernetes and podman sites
        sites = {
            "k8s": {
                "platform": "kubernetes",
                "namespace": "test"
            },
            "pod": {
                "platform": "podman",
                "namespace": "test"
            }
        }

        # Kubernetes-only step
        step = {"standard": "platform/access_your_kubernetes_clusters"}

        standard_steps_by_old_name = {}

        resolved = resolver.expand_standard_step(
            step,
            standard_steps,
            standard_steps_by_old_name,
            standard_text,
            sites
        )

        # Only k8s site should have commands
        self.assertIn("k8s", resolved["commands"])
        self.assertNotIn("pod", resolved["commands"])


if __name__ == "__main__":
    unittest.main()
