"""Kubernetes-specific operations for Phoenix."""

import json
import time
from typing import Optional, Tuple

from sketcher import utils
from sketcher.exceptions import SketcherError, SketcherTimeout


def check_environment():
    """Verify required programs are available.

    Raises:
        SketcherError: If required programs are missing
    """
    required = ["base64", "curl", "kubectl", "skupper"]

    for program in required:
        utils.check_program(program)


def resource_exists(resource: str) -> bool:
    """Check if a Kubernetes resource exists.

    Args:
        resource: Resource identifier (e.g., "deployment/frontend")

    Returns:
        True if resource exists, False otherwise
    """
    result = utils.run(
        f"kubectl get {resource}",
        check=False,
        quiet=True,
        stdout=utils.subprocess.DEVNULL,
        stderr=utils.subprocess.DEVNULL
    )
    return result.returncode == 0


def get_resource_json(resource: str, jsonpath: str = "") -> str:
    """Get resource field value using kubectl jsonpath.

    Args:
        resource: Resource identifier
        jsonpath: JSONPath expression (without outer braces)

    Returns:
        JSON value as string
    """
    return utils.call(f"kubectl get {resource} -o jsonpath='{{{jsonpath}}}'", quiet=True)


def await_resource(resource: str, timeout: int = 300, quiet: bool = False):
    """Wait for a Kubernetes resource to become available.

    For deployments, also waits for condition=available.

    Args:
        resource: Resource identifier (must contain "/")
        timeout: Timeout in seconds
        quiet: If True, suppress progress messages

    Raises:
        SketcherError: If resource format is invalid
        SketcherTimeout: If timeout is exceeded
    """
    if "/" not in resource:
        raise SketcherError(f"Resource must be in format 'type/name': {resource}")

    start_time = time.time()

    while True:
        utils.info("Waiting for {} to become available", resource, quiet=quiet)

        if resource_exists(resource):
            break

        if time.time() - start_time > timeout:
            raise SketcherTimeout(f"Timed out waiting for {resource}")

        time.sleep(5)

    # For deployments, wait for available condition
    if resource.startswith("deployment/"):
        try:
            utils.run(
                f"kubectl wait --for condition=available --timeout {timeout}s {resource}",
                quiet=True
            )
        except Exception:
            # Show logs on failure
            utils.run(f"kubectl logs {resource}", check=False)
            raise


def await_ingress(service: str, timeout: int = 300, quiet: bool = False) -> str:
    """Wait for LoadBalancer ingress hostname or IP.

    Args:
        service: Service identifier (must start with "service/")
        timeout: Timeout in seconds
        quiet: If True, suppress progress messages

    Returns:
        Hostname or IP address

    Raises:
        SketcherError: If service format is invalid or no hostname/IP found
        SketcherTimeout: If timeout is exceeded
    """
    if not service.startswith("service/"):
        raise SketcherError(f"Service must start with 'service/': {service}")

    start_time = time.time()

    # Wait for service to exist
    await_resource(service, timeout=timeout, quiet=quiet)

    # Wait for loadBalancer ingress
    while True:
        utils.info("Waiting for hostname or IP from {} to become available", service, quiet=quiet)

        json_str = get_resource_json(service, ".status.loadBalancer.ingress")

        if json_str:
            break

        if time.time() - start_time > timeout:
            raise SketcherTimeout(f"Timed out waiting for hostname or external IP for {service}")

        time.sleep(5)

    # Parse ingress data
    data = json.loads(json_str)

    if len(data):
        if "hostname" in data[0]:
            return data[0]["hostname"]

        if "ip" in data[0]:
            return data[0]["ip"]

    raise SketcherError(f"Failed to get hostname or IP from {service}")


def await_http_ok(
    service: str,
    url_template: str,
    user: Optional[str] = None,
    password: Optional[str] = None,
    timeout: int = 300,
    quiet: bool = False
):
    """Wait for HTTP 200 OK from a service.

    Args:
        service: Service identifier (must start with "service/")
        url_template: URL template with {} placeholder for host
        user: Optional basic auth username
        password: Optional basic auth password
        timeout: Timeout in seconds
        quiet: If True, suppress progress messages

    Raises:
        SketcherError: If service format is invalid
        SketcherTimeout: If timeout is exceeded
    """
    if not service.startswith("service/"):
        raise SketcherError(f"Service must start with 'service/': {service}")

    start_time = time.time()

    # Get ingress host
    host = await_ingress(service, timeout=timeout, quiet=quiet)

    # Build URL
    url = url_template.format(host)
    insecure = url.startswith("https")

    # Retry until HTTP OK
    while True:
        utils.info("Waiting for HTTP OK from {}", url, quiet=quiet)

        try:
            utils.http_get(url, insecure=insecure, auth=(user, password) if user else None)
            break
        except Exception:
            if time.time() - start_time > timeout:
                raise SketcherTimeout(f"Timed out waiting for HTTP OK from {url}")

            time.sleep(5)


def await_console_ok(timeout: int = 300, quiet: bool = False):
    """Wait for Skupper console to be ready.

    Waits for skupper-console-users secret and verifies console is accessible.

    Args:
        timeout: Timeout in seconds
        quiet: If True, suppress progress messages

    Raises:
        SketcherTimeout: If timeout is exceeded
    """
    # Wait for secret
    await_resource("secret/skupper-console-users", timeout=timeout, quiet=quiet)

    # Get admin password
    password = get_resource_json("secret/skupper-console-users", ".data.admin")
    password = utils.base64_decode(password)

    # Verify console is accessible
    await_http_ok("service/skupper", "https://{}:8010/", user="admin", password=password, timeout=timeout, quiet=quiet)


def await_port(port: int, host: str = "localhost", timeout: int = 300, quiet: bool = False):
    """Wait for a TCP port to accept connections.

    Args:
        port: Port number
        host: Hostname or IP (default: localhost)
        timeout: Timeout in seconds
        quiet: If True, suppress progress messages

    Raises:
        SketcherTimeout: If timeout is exceeded
    """
    import socket

    start_time = time.time()

    while True:
        utils.info("Waiting for port {} on {}", port, host, quiet=quiet)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            sock.close()
            # Port is open - give app time to fully initialize before health checks
            # Port-forward may accept connections before the app is ready to serve
            utils.info("Port {} is open, waiting 15s for application to stabilize...", port, quiet=quiet)
            time.sleep(15)
            break
        except (socket.error, OSError):
            if time.time() - start_time > timeout:
                raise SketcherTimeout(f"Timed out waiting for port {port} on {host}")

            time.sleep(5)
