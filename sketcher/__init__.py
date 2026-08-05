"""
Skewer - YAML processing and documentation generation for Skupper examples.

A library for resolving standard YAML templates and generating documentation.
"""

from .exceptions import SketcherError
from .model import Model, Site, Step, Command
from . import generator, resolver

__version__ = "0.2.0"  # Split: Python handles YAML processing, Go handles execution
__all__ = [
    "SketcherError",
    "Model",
    "Site",
    "Step",
    "Command",
    "generator",
    "resolver",
]
