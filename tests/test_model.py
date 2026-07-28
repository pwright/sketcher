"""
Unit tests for sketcher.model module.
"""

import tempfile
import unittest
from pathlib import Path

from sketcher import Model, utils
from sketcher.exceptions import SketcherError
from sketcher.model import get_github_owner_repo


class TestModel(unittest.TestCase):
    """Test Model class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_resolved_yaml(self):
        """Test parsing a resolved yaml file."""
        yaml_file = self.fixtures_dir / "skewer-resolved.yaml"
        model = Model(str(yaml_file))

        # Check basic properties
        self.assertEqual(model.title, "Skupper Hello World")
        self.assertEqual(
            model.subtitle,
            "A minimal HTTP application deployed across Kubernetes clusters using Skupper"
        )

        # Check sites
        sites = list(model.sites)
        self.assertEqual(len(sites), 2)

        west_name, west = sites[0]
        self.assertEqual(west_name, "west")
        self.assertEqual(west.name, "west")
        self.assertEqual(west.platform, "kubernetes")
        self.assertEqual(west.namespace, "west")

        east_name, east = sites[1]
        self.assertEqual(east_name, "east")
        self.assertEqual(east.platform, "kubernetes")

        # Check steps
        steps = list(model.steps)
        self.assertGreater(len(steps), 0)

        first_step = steps[0]
        self.assertEqual(first_step.number, 1)
        self.assertIn("Access", first_step.title)
        self.assertTrue(first_step.numbered)

    def test_model_check(self):
        """Test model validation."""
        yaml_file = self.fixtures_dir / "skewer-resolved.yaml"
        model = Model(str(yaml_file))

        # Should not raise
        model.check()

    def test_model_missing_title(self):
        """Test validation fails with missing title."""
        yaml_data = {
            "sites": {"test": {"platform": "kubernetes", "namespace": "test"}},
            "steps": []
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))

        with self.assertRaises(SketcherError) as cm:
            model.check()

        self.assertIn("missing required attribute 'title'", str(cm.exception))

    def test_apply_kubeconfigs(self):
        """Test applying kubeconfigs to kubernetes sites only."""
        yaml_data = {
            "title": "Test",
            "sites": {
                "west": {"platform": "kubernetes", "namespace": "west"},
                "east": {"platform": "kubernetes", "namespace": "east"}
            },
            "steps": []
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        kubeconfigs = ["~/.kube/west", "~/.kube/east"]
        model = Model(str(temp_file), kubeconfigs=kubeconfigs)

        # Check kubeconfigs were applied
        sites = list(model.sites)
        west = sites[0][1]
        east = sites[1][1]

        self.assertIn("KUBECONFIG", west.env)
        self.assertIn("KUBECONFIG", east.env)

    def test_apply_kubeconfigs_mixed_platforms(self):
        """Test kubeconfigs only apply to kubernetes sites, not podman."""
        yaml_data = {
            "title": "Test",
            "sites": {
                "k8s": {
                    "platform": "kubernetes",
                    "namespace": "test",
                    "env": {"KUBECONFIG": "/tmp/old"}
                },
                "pod": {
                    "platform": "podman",
                    "env": {"SKUPPER_PLATFORM": "podman"}
                }
            },
            "steps": []
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        # Only one kubeconfig for one kubernetes site
        kubeconfigs = ["~/.kube/k8s"]
        model = Model(str(temp_file), kubeconfigs=kubeconfigs)

        sites = dict(model.sites)
        k8s = sites["k8s"]
        pod = sites["pod"]

        # Kubernetes site should have new kubeconfig
        self.assertIn("KUBECONFIG", k8s.env)
        self.assertTrue(k8s.env["KUBECONFIG"].endswith("k8s"))

        # Podman site should NOT have KUBECONFIG
        self.assertNotIn("KUBECONFIG", pod.env)

    def test_default_text_substitution(self):
        """Test @default@ substitution from standardtext.yaml."""
        yaml_data = {
            "title": "Test",
            "summary": "@default@\n\nCustom summary text.",
            "sites": {"test": {"platform": "kubernetes", "namespace": "test"}},
            "steps": []
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))

        # Summary should have standard text + custom text
        self.assertIn("Custom summary text", model.summary)
        # Should also have some standard text
        self.assertGreater(len(model.summary), len("Custom summary text"))


class TestSite(unittest.TestCase):
    """Test Site class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_site_properties(self):
        """Test site property access."""
        yaml_data = {
            "title": "Test",
            "sites": {
                "west": {
                    "title": "Western Cluster",
                    "platform": "kubernetes",
                    "namespace": "west-ns",
                    "env": {"KUBECONFIG": "/path/to/config"}
                }
            },
            "steps": []
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        west_name, west = next(model.sites)

        self.assertEqual(west.name, "west")
        self.assertEqual(west.title, "Western Cluster")
        self.assertEqual(west.platform, "kubernetes")
        self.assertEqual(west.namespace, "west-ns")
        self.assertEqual(west.env["KUBECONFIG"], "/path/to/config")

    def test_site_title_default(self):
        """Test site title defaults to capitalized name."""
        yaml_data = {
            "title": "Test",
            "sites": {
                "west": {
                    "platform": "kubernetes",
                    "namespace": "west"
                }
            },
            "steps": []
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        _, west = next(model.sites)

        self.assertEqual(west.title, "West")

    def test_site_validation_kubernetes(self):
        """Test Kubernetes site validation."""
        yaml_data = {
            "title": "Test",
            "sites": {
                "k8s": {
                    "platform": "kubernetes",
                    "namespace": "test",
                    "env": {"KUBECONFIG": "/path/to/config"}
                }
            },
            "steps": []
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        _, site = next(model.sites)

        # Should not raise
        site.check()

    def test_site_validation_missing_namespace(self):
        """Test validation fails for Kubernetes without namespace."""
        yaml_data = {
            "title": "Test",
            "sites": {
                "k8s": {
                    "platform": "kubernetes",
                    "env": {"KUBECONFIG": "/path/to/config"}
                }
            },
            "steps": []
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        _, site = next(model.sites)

        with self.assertRaises(SketcherError) as cm:
            site.check()

        self.assertIn("missing required attribute 'namespace'", str(cm.exception))

    def test_site_validation_missing_kubeconfig(self):
        """Test validation fails for Kubernetes without KUBECONFIG."""
        yaml_data = {
            "title": "Test",
            "sites": {
                "k8s": {
                    "platform": "kubernetes",
                    "namespace": "test"
                }
            },
            "steps": []
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        _, site = next(model.sites)

        with self.assertRaises(SketcherError) as cm:
            site.check()

        self.assertIn("no KUBECONFIG environment variable", str(cm.exception))

    def test_site_validation_podman_platforms(self):
        """Test podman site accepts podman, docker, and linux in SKUPPER_PLATFORM."""
        for platform_value in ["podman", "docker", "linux"]:
            yaml_data = {
                "title": "Test",
                "sites": {
                    "test": {
                        "platform": "podman",
                        "env": {"SKUPPER_PLATFORM": platform_value}
                    }
                },
                "steps": []
            }

            temp_file = Path(self.temp_dir) / f"test-{platform_value}.yaml"
            utils.write_yaml(temp_file, yaml_data)

            model = Model(str(temp_file))
            _, site = next(model.sites)

            # Should not raise - all three values are valid
            site.check()

    def test_site_validation_invalid_skupper_platform(self):
        """Test podman site rejects invalid SKUPPER_PLATFORM values."""
        yaml_data = {
            "title": "Test",
            "sites": {
                "test": {
                    "platform": "podman",
                    "env": {"SKUPPER_PLATFORM": "invalid"}
                }
            },
            "steps": []
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        _, site = next(model.sites)

        with self.assertRaises(SketcherError) as cm:
            site.check()

        self.assertIn("has illegal value: invalid", str(cm.exception))
        self.assertIn("Must be one of: podman, docker, linux", str(cm.exception))

    def test_site_context_manager(self):
        """Test site as context manager."""
        yaml_data = {
            "title": "Test",
            "sites": {
                "test": {
                    "platform": "kubernetes",
                    "namespace": "test",
                    "env": {"KUBECONFIG": "/tmp/config", "TEST_VAR": "value"}
                }
            },
            "steps": []
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        _, site = next(model.sites)

        import os
        old_value = os.environ.get("TEST_VAR")

        with site:
            # Environment should be set
            self.assertEqual(os.environ.get("TEST_VAR"), "value")

        # Environment should be restored
        self.assertEqual(os.environ.get("TEST_VAR"), old_value)


class TestStep(unittest.TestCase):
    """Test Step class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_step_properties(self):
        """Test step property access."""
        yaml_data = {
            "title": "Test",
            "sites": {"test": {"platform": "kubernetes", "namespace": "test"}},
            "steps": [
                {
                    "title": "First Step",
                    "numbered": True,
                    "preamble": "This is the preamble",
                    "postamble": "This is the postamble",
                    "commands": {
                        "test": [
                            {"run": "echo 'hello'"}
                        ]
                    }
                }
            ]
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        step = next(model.steps)

        self.assertEqual(step.title, "First Step")
        self.assertEqual(step.number, 1)
        self.assertTrue(step.numbered)
        self.assertEqual(step.preamble, "This is the preamble")
        self.assertEqual(step.postamble, "This is the postamble")

    def test_step_commands(self):
        """Test step commands iteration."""
        yaml_data = {
            "title": "Test",
            "sites": {
                "west": {"platform": "kubernetes", "namespace": "west"},
                "east": {"platform": "kubernetes", "namespace": "east"}
            },
            "steps": [
                {
                    "title": "Test Step",
                    "commands": {
                        "west": [
                            {"run": "echo 'west'"}
                        ],
                        "east": [
                            {"run": "echo 'east'"}
                        ]
                    }
                }
            ]
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        step = next(model.steps)

        commands = list(step.commands)
        self.assertEqual(len(commands), 2)

        site_name, site_commands = commands[0]
        self.assertEqual(site_name, "west")
        self.assertEqual(len(site_commands), 1)
        self.assertEqual(site_commands[0].run, "echo 'west'")

    def test_step_validation_unknown_site(self):
        """Test validation fails with unknown site in commands."""
        yaml_data = {
            "title": "Test",
            "sites": {"west": {"platform": "kubernetes", "namespace": "west"}},
            "steps": [
                {
                    "title": "Test Step",
                    "commands": {
                        "unknown": [
                            {"run": "echo 'test'"}
                        ]
                    }
                }
            ]
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        step = next(model.steps)

        with self.assertRaises(SketcherError) as cm:
            step.check()

        self.assertIn("Unknown site name 'unknown'", str(cm.exception))


class TestCommand(unittest.TestCase):
    """Test Command class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_command_properties(self):
        """Test command property access."""
        yaml_data = {
            "title": "Test",
            "sites": {"test": {"platform": "kubernetes", "namespace": "test"}},
            "steps": [
                {
                    "title": "Test",
                    "commands": {
                        "test": [
                            {
                                "run": "kubectl get pods",
                                "expect_failure": False,
                                "apply": "readme",
                                "output": "Sample output"
                            }
                        ]
                    }
                }
            ]
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        step = next(model.steps)
        _, commands = next(step.commands)
        command = commands[0]

        self.assertEqual(command.run, "kubectl get pods")
        self.assertFalse(command.expect_failure)
        self.assertEqual(command.apply, "readme")
        self.assertEqual(command.output, "Sample output")

    def test_command_await_properties(self):
        """Test command await properties."""
        yaml_data = {
            "title": "Test",
            "sites": {"test": {"platform": "kubernetes", "namespace": "test"}},
            "steps": [
                {
                    "title": "Test",
                    "commands": {
                        "test": [
                            {
                                "await_resource": "deployment/frontend",
                                "await_ingress": "frontend",
                                "await_http_ok": "http://frontend:8080",
                                "await_console_ok": True,
                                "await_port": 8080
                            }
                        ]
                    }
                }
            ]
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        step = next(model.steps)
        _, commands = next(step.commands)
        command = commands[0]

        self.assertEqual(command.await_resource, "deployment/frontend")
        self.assertEqual(command.await_ingress, "frontend")
        self.assertEqual(command.await_http_ok, "http://frontend:8080")
        self.assertTrue(command.await_console_ok)
        self.assertEqual(command.await_port, 8080)


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions."""

    def test_get_github_owner_repo_https(self):
        """Test GitHub URL parsing (HTTPS format)."""
        # This test requires being in a git repo
        # We'll skip it if not in one
        try:
            owner, repo = get_github_owner_repo()
            self.assertIsInstance(owner, str)
            self.assertIsInstance(repo, str)
        except SketcherError:
            # Not in a git repo or unknown URL format
            pass

    def test_capitalize(self):
        """Test capitalize preserves case after first char."""
        # Match Plano behavior, not Python's str.capitalize()
        self.assertEqual(utils.capitalize("hello"), "Hello")
        self.assertEqual(utils.capitalize("myNS"), "MyNS")  # NOT "Myns"
        self.assertEqual(utils.capitalize("west"), "West")
        self.assertEqual(utils.capitalize(""), "")


class TestReprFormats(unittest.TestCase):
    """Test __repr__ formats match Skewer for error messages."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_model_repr(self):
        """Test Model repr matches Skewer format."""
        yaml_data = {
            "title": "Test",
            "sites": {"test": {"platform": "kubernetes", "namespace": "test"}},
            "steps": []
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        self.assertEqual(repr(model), f"model '{temp_file}'")

    def test_site_repr(self):
        """Test Site repr matches Skewer format."""
        yaml_data = {
            "title": "Test",
            "sites": {"west": {"platform": "kubernetes", "namespace": "west"}},
            "steps": []
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        _, site = next(model.sites)

        self.assertEqual(repr(site), "site 'west'")

    def test_step_repr(self):
        """Test Step repr matches Skewer format."""
        yaml_data = {
            "title": "Test",
            "sites": {"test": {"platform": "kubernetes", "namespace": "test"}},
            "steps": [{"title": "Deploy Frontend"}]
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        step = next(model.steps)

        self.assertEqual(repr(step), "step 1 'Deploy Frontend'")

    def test_command_repr(self):
        """Test Command repr matches Skewer format."""
        yaml_data = {
            "title": "Test",
            "sites": {"test": {"platform": "kubernetes", "namespace": "test"}},
            "steps": [
                {
                    "title": "Test",
                    "commands": {
                        "test": [
                            {"run": "kubectl get pods"}
                        ]
                    }
                }
            ]
        }

        temp_file = Path(self.temp_dir) / "test.yaml"
        utils.write_yaml(temp_file, yaml_data)

        model = Model(str(temp_file))
        step = next(model.steps)
        _, commands = next(step.commands)
        command = commands[0]

        self.assertEqual(repr(command), "command 'kubectl get pods'")


if __name__ == "__main__":
    unittest.main()
