"""
Phoenix utilities module.

Standard library replacements for Plano functions.
Clean, readable implementations using Python 3 stdlib.
"""

import base64
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.parse
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from .exceptions import SketcherError, SketcherProcessError, SketcherTimeout


# ==============================================================================
# Logging Configuration
# ==============================================================================
#
# Phoenix logging system provides:
# - Color-coded output (green=success, red=error, yellow=warning, cyan=info)
# - Quiet mode support (suppress progress messages for scripting/automation)
# - Visual operation hierarchy (nested operations with tree-like display)
# - TTY detection (automatic color enable/disable based on terminal)
#
# Key functions:
# - info/notice/warn/error: Standard logging levels with quiet support
# - cprint/eprint: Color printing and stderr output
# - operation(): Context manager for nested operations with timing
# - console_color(): Context manager for colored blocks
#
# Environment variables:
# - PHOENIX_COLOR: Force enable color output even in non-TTY
# ==============================================================================

_logging_prefix = ""
_operation_depth = 0

# ANSI color codes for terminal output
_COLOR_CODES = {
    "black": "[30",
    "red": "[31",
    "green": "[32",
    "yellow": "[33",
    "blue": "[34",
    "magenta": "[35",
    "cyan": "[36",
    "white": "[37",
    "gray": "[90",
}
_COLOR_RESET = "[0m"


def _get_color_code(color: str, bright: bool = False) -> str:
    """Get ANSI color code."""
    elems = [_COLOR_CODES[color]]
    if bright:
        elems.append(";1")
    elems.append("m")
    return "".join(elems)


def _is_color_enabled(file) -> bool:
    """Check if color output is supported."""
    return (os.getenv("PHOENIX_COLOR") is not None
            or (hasattr(file, "isatty") and file.isatty()))


@contextmanager
def console_color(color: str, bright: bool = False, file=sys.stdout):
    """Context manager for colored output."""
    enabled = _is_color_enabled(file)
    if enabled:
        print(_get_color_code(color, bright), file=file, end="", flush=True)
    try:
        yield
    finally:
        if enabled:
            print(_COLOR_RESET, file=file, end="", flush=True)


def cprint(message: str, color: Optional[str] = None, bright: bool = False,
           file=sys.stdout, **kwargs):
    """Print with optional color."""
    if color and _is_color_enabled(file):
        message = f"{_get_color_code(color, bright)}{message}{_COLOR_RESET}"
    print(message, file=file, **kwargs)


def eprint(*args, **kwargs):
    """Print to stderr."""
    print(*args, file=sys.stderr, **kwargs)


def configure_logging(level=logging.INFO):
    """Configure logging with custom formatter."""
    logging.basicConfig(
        level=level,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def debug(message: str, *args, quiet: bool = False):
    """Log a debug message (only shown with DEBUG level)."""
    if quiet:
        return
    if args:
        message = message.format(*args)
    if _logging_prefix:
        message = f"{_logging_prefix}: {message}"
    logging.debug(message)


def info(message: str, *args, quiet: bool = False):
    """Log an info message (can be suppressed with quiet)."""
    if quiet:
        return
    if args:
        message = message.format(*args)
    if _logging_prefix:
        message = f"{_logging_prefix}: {message}"
    logging.info(message)


def notice(message: str, *args, quiet: bool = False):
    """Log an info message (replaces plano.notice)."""
    if quiet:
        return
    if args:
        message = message.format(*args)
    if _logging_prefix:
        message = f"{_logging_prefix}: {message}"
    logging.info(message)


def warn(message: str, *args, quiet: bool = False):
    """Log a warning message (replaces plano.warn)."""
    if quiet:
        return
    if args:
        message = message.format(*args)
    if _logging_prefix:
        message = f"{_logging_prefix}: {message}"
    logging.warning(message)


def error(message: str, *args, quiet: bool = False):
    """Log an error message (replaces plano.error)."""
    if quiet:
        return
    if args:
        message = message.format(*args)
    if _logging_prefix:
        message = f"{_logging_prefix}: {message}"
    logging.error(message)


def fail(message: str, *args):
    """Log error and raise SketcherError (replaces plano.fail)."""
    if args:
        message = message.format(*args)
    error(message)
    raise SketcherError(message)


@contextmanager
def logging_prefix(prefix: str):
    """Context manager to set logging prefix."""
    global _logging_prefix
    old_prefix = _logging_prefix
    _logging_prefix = prefix
    try:
        yield
    finally:
        _logging_prefix = old_prefix


@contextmanager
def operation(name: str, quiet: bool = False):
    """Context manager for nested operations with visual hierarchy.

    Provides visual feedback for long-running operations with:
    - Start indicator (→) in cyan
    - Success indicator (✓) in green with timing
    - Failure indicator (✗) in red with timing
    - Automatic indentation for nested operations

    Example:
        with operation("Running tests"):
            with operation("Unit tests"):
                run_unit_tests()
            with operation("Integration tests"):
                run_integration_tests()

    Output:
        → Running tests
          → Unit tests
          ✓ Unit tests (2.34s)
          → Integration tests
          ✓ Integration tests (5.67s)
        ✓ Running tests (8.01s)
    """
    global _operation_depth

    start = time.time()

    if not quiet:
        indent = "  " * _operation_depth
        cprint(f"{indent}→ {name}", color="cyan")

    _operation_depth += 1

    try:
        yield
    except Exception:
        _operation_depth -= 1
        if not quiet:
            duration = time.time() - start
            indent = "  " * _operation_depth
            cprint(f"{indent}✗ {name} ({duration:.2f}s)", color="red")
        raise
    else:
        _operation_depth -= 1
        if not quiet:
            duration = time.time() - start
            indent = "  " * _operation_depth
            cprint(f"{indent}✓ {name} ({duration:.2f}s)", color="green")


# ==============================================================================
# File I/O
# ==============================================================================

def read(path: Union[str, Path]) -> str:
    """Read file contents as string (replaces plano.read)."""
    return Path(path).read_text()


def write(path: Union[str, Path], content: str):
    """Write string content to file (replaces plano.write)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def read_yaml(path: Union[str, Path]) -> Any:
    """Read and parse YAML file (replaces plano.read_yaml)."""
    content = read(path)
    return yaml.safe_load(content)


def write_yaml(path: Union[str, Path], data: Any):
    """Write data to YAML file (replaces plano.write_yaml)."""
    content = write_yaml_to_string(data)
    write(path, content)


def write_yaml_to_string(data: Any) -> str:
    """Convert data to YAML string."""
    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def read_json(path: Union[str, Path]) -> Any:
    """Read and parse JSON file (replaces plano.read_json)."""
    content = read(path)
    return json.loads(content)


def write_json(path: Union[str, Path], data: Any):
    """Write data to JSON file (replaces plano.write_json)."""
    content = json.dumps(data, indent=2)
    write(path, content + "\n")


def parse_json(s: str) -> Any:
    """Parse JSON string (replaces plano.parse_json)."""
    return json.loads(s)


def parse_yaml(s: str) -> Any:
    """Parse YAML string (replaces plano.parse_yaml)."""
    return yaml.safe_load(s)


# ==============================================================================
# Path Operations
# ==============================================================================

def join(*paths) -> str:
    """Join path components (replaces plano.join)."""
    return os.path.join(*paths)


def absolute_path(path: Union[str, Path]) -> str:
    """Return absolute path (replaces plano.absolute_path)."""
    return str(Path(path).resolve())


def parent_dir(path: Union[str, Path]) -> str:
    """Return parent directory (replaces plano.parent_dir)."""
    return str(Path(path).parent)


def file_name(path: Union[str, Path]) -> str:
    """Return file name (replaces plano.file_name)."""
    return Path(path).name


def expand(path: str) -> str:
    """Expand ~ and environment variables (replaces plano.expand)."""
    return os.path.expanduser(os.path.expandvars(path))


def exists(path: Union[str, Path]) -> bool:
    """Check if path exists (replaces plano.exists)."""
    return Path(path).exists()


def remove(path: Union[str, Path]):
    """Remove file or directory (replaces plano.remove)."""
    path = Path(path)
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def make_dir(path: Union[str, Path]):
    """Create directory (replaces plano.make_dir)."""
    Path(path).mkdir(parents=True, exist_ok=True)


def list_dir(path: Union[str, Path]):
    """List directory contents (replaces plano.list_dir)."""
    return [str(p) for p in Path(path).iterdir()]


def find(path: Union[str, Path], pattern: str = "*"):
    """Find files matching pattern (replaces plano.find)."""
    return [str(p) for p in Path(path).rglob(pattern)]


# ==============================================================================
# Process Management
# ==============================================================================

def run(command: str,
        shell: bool = True,
        check: bool = True,
        quiet: bool = False,
        stdin: Optional[str] = None,
        **kwargs) -> subprocess.CompletedProcess:
    """
    Run command and return result (replaces plano.run).

    Args:
        command: Shell command to run
        shell: Run through shell
        check: Raise exception on non-zero exit
        quiet: Don't log command
        stdin: Optional input to pass to command
        **kwargs: Additional subprocess.run arguments

    Returns:
        CompletedProcess instance

    Raises:
        SketcherProcessError: If command fails and check=True
    """
    if not quiet:
        notice(f"Running: {command}")

    try:
        input_data = stdin.encode() if stdin else None

        # Only use capture_output if stdout/stderr not explicitly set
        use_capture = 'stdout' not in kwargs and 'stderr' not in kwargs

        result = subprocess.run(
            command,
            shell=shell,
            check=check,
            capture_output=use_capture,
            input=input_data,
            **kwargs
        )

        if not quiet and use_capture and result.stdout:
            sys.stdout.buffer.write(result.stdout)
            sys.stdout.flush()

        return result

    except subprocess.CalledProcessError as e:
        stderr_text = e.stderr.decode() if e.stderr else ""
        stdout_text = e.stdout.decode() if e.stdout else ""
        raise SketcherProcessError(e.returncode, e.cmd, stdout_text, stderr_text)


def call(command: str, quiet: bool = False, **kwargs) -> str:
    """
    Run command and return stdout as string (replaces plano.call).

    Args:
        command: Shell command to run
        quiet: Don't log command
        **kwargs: Additional subprocess.run arguments

    Returns:
        Command stdout as string (decoded, stripped)
    """
    result = run(command, quiet=quiet, **kwargs)
    return result.stdout.decode().strip()


def start_process(command: str,
                  stdout_file: Optional[str] = None,
                  stderr_file: Optional[str] = None,
                  **kwargs) -> subprocess.Popen:
    """
    Start background process (replaces plano.start_process).

    Args:
        command: Shell command to run
        stdout_file: File to redirect stdout to
        stderr_file: File to redirect stderr to
        **kwargs: Additional Popen arguments

    Returns:
        Popen instance
    """
    notice(f"Starting: {command}")

    stdout = open(stdout_file, 'w') if stdout_file else subprocess.PIPE
    stderr = open(stderr_file, 'w') if stderr_file else subprocess.PIPE

    return subprocess.Popen(
        command,
        shell=True,
        stdout=stdout,
        stderr=stderr,
        **kwargs
    )


def stop_process(proc: subprocess.Popen, timeout: int = 5):
    """
    Stop process gracefully (replaces plano.stop_process).

    Args:
        proc: Process to stop
        timeout: Seconds to wait before force kill
    """
    if proc.poll() is not None:
        return  # Already stopped

    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


# ==============================================================================
# Temporary Files
# ==============================================================================

def make_temp_dir() -> str:
    """Create temporary directory (replaces plano.make_temp_dir)."""
    return tempfile.mkdtemp()


def make_temp_file() -> str:
    """Create temporary file (replaces plano.make_temp_file)."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    return path


@contextmanager
def temp_dir():
    """Context manager for temporary directory."""
    dir_path = make_temp_dir()
    try:
        yield dir_path
    finally:
        shutil.rmtree(dir_path, ignore_errors=True)


@contextmanager
def temp_file():
    """Context manager for temporary file."""
    file_path = make_temp_file()
    try:
        yield file_path
    finally:
        try:
            os.unlink(file_path)
        except OSError:
            pass


# ==============================================================================
# Environment
# ==============================================================================

@contextmanager
def working_env(**env_vars):
    """
    Context manager to temporarily set environment variables.
    (replaces plano.working_env)
    """
    old_env = {}
    for key, value in env_vars.items():
        old_env[key] = os.environ.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = str(value)

    try:
        yield
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


# ==============================================================================
# HTTP Operations
# ==============================================================================

def http_get(url: str,
             auth: Optional[tuple] = None,
             insecure: bool = False,
             timeout: int = 30) -> str:
    """
    HTTP GET request (replaces plano.http_get).

    Args:
        url: URL to fetch
        auth: Optional (username, password) tuple for basic auth
        insecure: Allow insecure HTTPS
        timeout: Request timeout in seconds

    Returns:
        Response body as string
    """
    import ssl

    request = urllib.request.Request(url)

    if auth:
        username, password = auth
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        request.add_header("Authorization", f"Basic {credentials}")

    context = None
    if insecure:
        context = ssl._create_unverified_context()

    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return response.read().decode()


def http_get_json(url: str, **kwargs) -> Any:
    """
    HTTP GET request returning JSON (replaces plano.http_get_json).

    Args:
        url: URL to fetch
        **kwargs: Additional http_get arguments

    Returns:
        Parsed JSON data
    """
    content = http_get(url, **kwargs)
    return json.loads(content)


# ==============================================================================
# Utilities
# ==============================================================================


def get_github_owner_repo() -> tuple[str, str]:
    """Get GitHub owner and repo from git remote origin URL.

    Supports both SSH and HTTPS git URLs:
    - git@github.com:owner/repo.git
    - https://github.com/owner/repo.git

    Returns:
        (owner, repo) tuple

    Raises:
        SketcherError: If git remote origin URL is not a GitHub URL
    """
    from urllib.parse import urlparse

    check_program("git")

    url = call("git remote get-url origin", quiet=True)
    result = urlparse(url)

    # SSH format: git@github.com:owner/repo.git
    if result.scheme == "" and result.path.startswith("git@github.com:"):
        path = result.path.removeprefix("git@github.com:")
        path = path.removesuffix(".git")
        parts = path.split("/", 1)
        return (parts[0], parts[1])

    # HTTPS format: https://github.com/owner/repo.git
    if result.scheme in ("http", "https") and result.netloc == "github.com":
        path = result.path.removeprefix("/")
        path = path.removesuffix(".git")
        parts = path.split("/", 1)
        return (parts[0], parts[1])

    raise SketcherError(f"Unknown git remote origin URL format: {url}")

def check_program(name: str):
    """
    Check if program is available (replaces plano.check_program).

    Raises:
        SketcherError: If program not found
    """
    if shutil.which(name) is None:
        fail(f"Required program '{name}' is not available")


def await_port(port: int, host: str = "localhost", timeout: int = 300):
    """
    Wait for port to be available (replaces plano.await_port).

    Args:
        port: Port number
        host: Host to connect to
        timeout: Timeout in seconds

    Raises:
        SketcherTimeout: If port not available within timeout
    """
    start_time = time.time()

    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((host, port))
            sock.close()
            return
        except (socket.error, socket.timeout):
            if time.time() - start_time > timeout:
                raise SketcherTimeout(f"Port {port} on {host}", timeout)
            time.sleep(5)


def get_time() -> float:
    """Get current time in seconds (replaces plano.get_time)."""
    return time.time()


def sleep(seconds: float):
    """Sleep for specified seconds (replaces plano.sleep)."""
    time.sleep(seconds)


def base64_encode(data: Union[str, bytes]) -> str:
    """Encode data to base64 (replaces plano.base64_encode)."""
    if isinstance(data, str):
        data = data.encode()
    return base64.b64encode(data).decode()


def base64_decode(data: str) -> str:
    """Decode base64 data (replaces plano.base64_decode)."""
    return base64.b64decode(data).decode()


def get_user() -> str:
    """Get current username (replaces plano.get_user)."""
    return os.getenv("USER", "unknown")


def get_hostname() -> str:
    """Get hostname (replaces plano.get_hostname)."""
    return socket.gethostname()


def capitalize(string: str) -> str:
    """
    Capitalize first character only (replaces plano.capitalize).

    Unlike Python's str.capitalize(), this only uppercases the first
    character without lowercasing the rest.

    Examples:
        capitalize("hello") → "Hello"
        capitalize("myNS") → "MyNS" (not "Myns")
    """
    if not string:
        return ""
    return string[0].upper() + string[1:]


def http_health_check(url: str, max_attempts: int = 10, delay: int = 3) -> bool:
    """
    Perform HTTP health check with retries.

    Args:
        url: URL to check
        max_attempts: Maximum number of attempts
        delay: Seconds to wait between attempts

    Returns:
        True if successful, False otherwise
    """
    import urllib.request
    import urllib.error

    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    notice(f"Health check succeeded for {url}")
                    return True
        except (urllib.error.URLError, OSError) as e:
            if attempt < max_attempts:
                notice(f"Health check attempt {attempt}/{max_attempts} failed, retrying in {delay}s...")
                sleep(delay)
            else:
                error(f"Health check failed after {max_attempts} attempts: {e}")
                return False

    return False
