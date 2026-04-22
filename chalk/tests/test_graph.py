"""Tests for chalk.graph: Node, Edge, Graph, PathHighlight."""
from __future__ import annotations

import math
import numpy as np
import pytest

from chalk.graph import Node, Edge, Graph, PathHighlight
from chalk.vgroup import VGroup
from chalk.scene import Scene
from chalk.animation import FadeIn
from chalk.camera import Camera2D


class _NullSink:
    def write(self, _): pass


def _attach(scene):
    cam = Camera2D()
    cam.pixel_width = 320
    cam.pixel_height = 180
    scene._attach(_NullSink(), camera=cam)


# ── Node ─────────────────────────────────────────────────────────────────────

def test_node_is_vgroup():
    n = Node("A", position=(0.0, 0.0))
    assert isinstance(n, VGroup)


def test_node_stores_label():
    n = Node("X", position=(1.0, 2.0))
    assert n._label == "X"


def test_node_stores_position():
    n = Node("A", position=(3.0, -1.0))
    assert n.position == pytest.approx([3.0, -1.0])


def test_node_has_circle_and_label():
    n = Node("B")
    # circle + MathTex VGroup
    assert len(n.submobjects) == 2


# ── Edge ─────────────────────────────────────────────────────────────────────

def test_edge_directed():
    a = Node("A", position=(0.0, 0.0))
    b = Node("B", position=(2.0, 0.0))
    e = Edge(a, b, directed=True)
    assert isinstance(e, VGroup)
    assert len(e.submobjects) == 1  # arrow only


def test_edge_undirected():
    a = Node("A", position=(0.0, 0.0))
    b = Node("B", position=(2.0, 0.0))
    e = Edge(a, b, directed=False)
    assert len(e.submobjects) == 1  # line only


def test_edge_with_weight():
    a = Node("A", position=(0.0, 0.0))
    b = Node("B", position=(3.0, 0.0))
    e = Edge(a, b, weight="5")
    assert len(e.submobjects) == 2  # arrow + label


def test_edge_coincident_nodes():
    a = Node("A", position=(0.0, 0.0))
    e = Edge(a, a)
    assert isinstance(e, VGroup)


# ── Graph ─────────────────────────────────────────────────────────────────────

def test_graph_from_adjacency_circular():
    adj = {"A": ["B", "C"], "B": ["C"], "C": []}
    g = Graph.from_adjacency(adj, layout="circular")
    assert isinstance(g, VGroup)
    assert len(g.nodes) == 3
    assert len(g.edges) == 3  # A→B, A→C, B→C


def test_graph_node_positions_circular():
    adj = {"A": [], "B": [], "C": [], "D": []}
    g = Graph.from_adjacency(adj, layout="circular", radius=2.0)
    positions = [n.position for n in g.nodes]
    radii = [float(np.linalg.norm(p)) for p in positions]
    # All nodes should be approximately on the circle
    for r in radii:
        assert r == pytest.approx(2.0, abs=0.02)


def test_graph_from_adjacency_spring():
    adj = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
    g = Graph.from_adjacency(adj, layout="spring")
    assert len(g.nodes) == 4


def test_graph_from_adjacency_spring_convergence():
    """Spring layout should keep nodes within ~2x the radius bound."""
    adj = {"1": ["2", "3"], "2": ["4"], "3": ["4"], "4": ["5"], "5": []}
    g = Graph.from_adjacency(adj, layout="spring", radius=2.5)
    for n in g.nodes:
        r = float(np.linalg.norm(n.position))
        assert r <= 3.0, f"Node {n._label} at radius {r:.2f} — outside 2x bound"


def test_graph_from_adjacency_tree():
    adj = {"root": ["L", "R"], "L": ["LL", "LR"], "R": [], "LL": [], "LR": []}
    g = Graph.from_adjacency(adj, layout="tree")
    assert len(g.nodes) == 5


def test_graph_from_adjacency_weighted():
    adj = {"A": [("B", "3"), ("C", "7")], "B": [], "C": []}
    g = Graph.from_adjacency(adj, layout="circular")
    assert len(g.edges) == 2


def test_graph_renders():
    class GScene(Scene):
        def construct(self):
            adj = {"A": ["B", "C"], "B": ["C"], "C": []}
            g = Graph.from_adjacency(adj, layout="circular", radius=1.5)
            self.add(g)
            self.play(FadeIn(g, run_time=0.4))
            self.wait(0.2)
    scene = GScene()
    _attach(scene)
    scene.construct()


# ── PathHighlight ──────────────────────────────────────────────────────────────

def test_path_highlight_is_vgroup():
    adj = {"A": ["B", "C"], "B": ["C"], "C": []}
    g = Graph.from_adjacency(adj, layout="circular")
    ph = PathHighlight(g, ["A", "B", "C"])
    assert isinstance(ph, VGroup)


def test_path_highlight_single_node():
    adj = {"A": ["B"], "B": []}
    g = Graph.from_adjacency(adj, layout="circular")
    ph = PathHighlight(g, ["A"])
    # 1 ring, 0 arrows
    assert len(ph.submobjects) == 1


def test_path_highlight_two_nodes():
    adj = {"A": ["B"], "B": []}
    g = Graph.from_adjacency(adj, layout="circular")
    ph = PathHighlight(g, ["A", "B"])
    # 2 rings + 1 arrow
    assert len(ph.submobjects) == 3


def test_path_highlight_renders():
    class PHScene(Scene):
        def construct(self):
            adj = {"S": ["A", "B"], "A": ["T"], "B": ["T"], "T": []}
            g = Graph.from_adjacency(adj, layout="circular", radius=1.5)
            ph = PathHighlight(g, ["S", "A", "T"])
            self.add(g)
            self.play(FadeIn(g, run_time=0.3))
            self.add(ph)
            self.play(FadeIn(ph, run_time=0.4))
            self.wait(0.3)
    scene = PHScene()
    _attach(scene)
    scene.construct()
