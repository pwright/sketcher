"""
Unit tests for sketcher.utils module.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

import yaml

from sketcher import utils
from sketcher.exceptions import SketcherError, SketcherProcessError


class TestFileIO(unittest.TestCase):
    """Test file I/O functions."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_read_write(self):
        """Test read and write functions."""
        file_path = Path(self.temp_dir) / "test.txt"
        content = "Hello, Sketcher!"

        utils.write(file_path, content)
        self.assertTrue(file_path.exists())

        result = utils.read(file_path)
        self.assertEqual(result, content)

    def test_read_write_yaml(self):
        """Test YAML read and write."""
        file_path = Path(self.temp_dir) / "test.yaml"
        data = {"title": "Test", "items": ["one", "two", "three"]}

        utils.write_yaml(file_path, data)
        result = utils.read_yaml(file_path)

        self.assertEqual(result, data)

    def test_read_write_json(self):
        """Test JSON read and write."""
        file_path = Path(self.temp_dir) / "test.json"
        data = {"name": "Sketcher", "version": "0.1.0"}

        utils.write_json(file_path, data)
        result = utils.read_json(file_path)

        self.assertEqual(result, data)

    def test_parse_json(self):
        """Test JSON parsing."""
        json_str = '{"key": "value"}'
        result = utils.parse_json(json_str)
        self.assertEqual(result, {"key": "value"})

    def test_parse_yaml(self):
        """Test YAML parsing."""
        yaml_str = "key: value\nlist:\n  - item1\n  - item2"
        result = utils.parse_yaml(yaml_str)
        self.assertEqual(result, {"key": "value", "list": ["item1", "item2"]})


class TestPathOperations(unittest.TestCase):
    """Test path operation functions."""

    def test_join(self):
        """Test path joining."""
        result = utils.join("path", "to", "file.txt")
        expected = os.path.join("path", "to", "file.txt")
        self.assertEqual(result, expected)

    def test_absolute_path(self):
        """Test absolute path resolution."""
        result = utils.absolute_path(".")
        self.assertTrue(os.path.isabs(result))

    def test_parent_dir(self):
        """Test parent directory."""
        result = utils.parent_dir("/path/to/file.txt")
        self.assertEqual(result, "/path/to")

    def test_file_name(self):
        """Test file name extraction."""
        result = utils.file_name("/path/to/file.txt")
        self.assertEqual(result, "file.txt")

    def test_expand(self):
        """Test path expansion."""
        os.environ["TEST_VAR"] = "/test"
        result = utils.expand("$TEST_VAR/file.txt")
        self.assertEqual(result, "/test/file.txt")

    def test_exists(self):
        """Test path existence check."""
        self.assertTrue(utils.exists("/"))
        self.assertFalse(utils.exists("/nonexistent/path"))


class TestProcessManagement(unittest.TestCase):
    """Test process management functions."""

    def test_call_success(self):
        """Test successful command execution."""
        result = utils.call("echo 'Hello'", quiet=True)
        self.assertEqual(result, "Hello")

    def test_call_failure(self):
        """Test failed command raises exception."""
        with self.assertRaises(SketcherProcessError) as cm:
            utils.call("exit 1", quiet=True)

        self.assertEqual(cm.exception.returncode, 1)

    def test_run_with_output(self):
        """Test run command with output."""
        result = utils.run("echo 'test output'", quiet=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"test output", result.stdout)


class TestTemporaryFiles(unittest.TestCase):
    """Test temporary file functions."""

    def test_make_temp_dir(self):
        """Test temporary directory creation."""
        temp_dir = utils.make_temp_dir()
        self.assertTrue(os.path.isdir(temp_dir))
        os.rmdir(temp_dir)

    def test_make_temp_file(self):
        """Test temporary file creation."""
        temp_file = utils.make_temp_file()
        self.assertTrue(os.path.isfile(temp_file))
        os.unlink(temp_file)

    def test_temp_dir_context(self):
        """Test temporary directory context manager."""
        with utils.temp_dir() as temp_path:
            self.assertTrue(os.path.isdir(temp_path))
            test_file = Path(temp_path) / "test.txt"
            test_file.write_text("content")

        # Directory should be cleaned up
        self.assertFalse(os.path.exists(temp_path))

    def test_temp_file_context(self):
        """Test temporary file context manager."""
        with utils.temp_file() as temp_path:
            self.assertTrue(os.path.isfile(temp_path))
            Path(temp_path).write_text("content")

        # File should be cleaned up
        self.assertFalse(os.path.exists(temp_path))


class TestEnvironment(unittest.TestCase):
    """Test environment functions."""

    def test_working_env(self):
        """Test working_env context manager."""
        original_value = os.environ.get("TEST_ENV_VAR")

        with utils.working_env(TEST_ENV_VAR="test_value"):
            self.assertEqual(os.environ["TEST_ENV_VAR"], "test_value")

        # Should be restored
        self.assertEqual(os.environ.get("TEST_ENV_VAR"), original_value)

    def test_working_env_multiple(self):
        """Test working_env with multiple variables."""
        with utils.working_env(VAR1="value1", VAR2="value2"):
            self.assertEqual(os.environ["VAR1"], "value1")
            self.assertEqual(os.environ["VAR2"], "value2")


class TestUtilities(unittest.TestCase):
    """Test utility functions."""

    def test_check_program_exists(self):
        """Test check_program with existing program."""
        utils.check_program("ls")  # Should not raise

    def test_check_program_missing(self):
        """Test check_program with missing program."""
        with self.assertRaises(SketcherError):
            utils.check_program("nonexistent_program_xyz")

    def test_base64_encode_string(self):
        """Test base64 encoding of string."""
        result = utils.base64_encode("Hello")
        self.assertEqual(result, "SGVsbG8=")

    def test_base64_encode_bytes(self):
        """Test base64 encoding of bytes."""
        result = utils.base64_encode(b"Hello")
        self.assertEqual(result, "SGVsbG8=")

    def test_base64_decode(self):
        """Test base64 decoding."""
        result = utils.base64_decode("SGVsbG8=")
        self.assertEqual(result, "Hello")

    def test_get_time(self):
        """Test get_time returns float."""
        result = utils.get_time()
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_get_user(self):
        """Test get_user returns string."""
        result = utils.get_user()
        self.assertIsInstance(result, str)

    def test_get_hostname(self):
        """Test get_hostname returns string."""
        result = utils.get_hostname()
        self.assertIsInstance(result, str)

    def test_capitalize(self):
        """Test capitalize preserves case after first character."""
        # Should match Plano behavior, not Python's str.capitalize()
        self.assertEqual(utils.capitalize("hello"), "Hello")
        self.assertEqual(utils.capitalize("myNS"), "MyNS")  # NOT "Myns"
        self.assertEqual(utils.capitalize("west"), "West")
        self.assertEqual(utils.capitalize("WEST"), "WEST")
        self.assertEqual(utils.capitalize(""), "")


class TestLogging(unittest.TestCase):
    """Test logging functions."""

    def test_logging_prefix_context(self):
        """Test logging_prefix context manager."""
        with utils.logging_prefix("test_prefix"):
            self.assertEqual(utils._logging_prefix, "test_prefix")

        # Should be restored
        self.assertEqual(utils._logging_prefix, "")


if __name__ == "__main__":
    unittest.main()
