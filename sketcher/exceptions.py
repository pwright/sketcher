"""
Sketcher exceptions module.

Custom exception classes for Sketcher framework.
"""


class SketcherError(Exception):
    """Base exception for all Sketcher errors."""
    pass


class SketcherProcessError(SketcherError):
    """Raised when a subprocess fails."""

    def __init__(self, returncode, cmd, stdout=None, stderr=None):
        self.returncode = returncode
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr

        message = f"Command failed with exit code {returncode}: {cmd}"
        if stderr:
            message += f"\n{stderr}"

        super().__init__(message)


class SketcherTimeout(SketcherError):
    """Raised when an await operation times out."""

    def __init__(self, operation, timeout):
        self.operation = operation
        self.timeout = timeout
        message = f"{operation} timed out after {timeout} seconds"
        super().__init__(message)
