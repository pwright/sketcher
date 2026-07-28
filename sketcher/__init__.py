"""
Sketcher - Python 3 framework for Skupper examples.

A library for documenting and testing Skupper examples.
"""

from .exceptions import SketcherError, SketcherProcessError, SketcherTimeout
from .model import Model, Site, Step, Command
from . import generator, executor, resolver, demo, kubernetes, minikube, kind

__version__ = "0.1.1"  # TODO (Nov 2026): Auto-read from pyproject.toml using tomllib after dropping Python 3.10 support
__all__ = [
    "SketcherError",
    "SketcherProcessError",
    "SketcherTimeout",
    "Model",
    "Site",
    "Step",
    "Command",
    "generator",
    "executor",
    "resolver",
    "demo",
    "kubernetes",
    "minikube",
    "kind",
]
