"""montology-canvas: the ontology as a graph, served locally.

A FACE on the engine, never a second writer — every mutation goes through the
same functions the CLI calls, so every law applies identically whether a human
typed it or dragged it.
"""

from .graph import graph

__all__ = ["graph"]
