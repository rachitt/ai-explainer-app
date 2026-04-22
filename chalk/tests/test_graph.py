"""Tests for chalk.graph: Node, Edge, Graph, PathHighlight."""
from __future__ import annotations

import pytest

from chalk.graph import Node, Edge, Graph, PathHighlight
from chalk.vgroup import VGroup


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


def test_node_radius_fits_multi_char_label():
    n = Node("root")
    assert n.fitted_radius > 0.35


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


def test_edge_uses_fitted_radius():
    a = Node("A", position=(0.0, 0.0))
    b = Node("root", position=(2.0, 0.0))
    Edge(a, b)


# ── Graph ─────────────────────────────────────────────────────────────────────

def test_manual_graph_construction():
    nodes = [
        Node("A", position=(-2.0, 0.0)),
        Node("B", position=(0.0, 0.0)),
        Node("C", position=(2.0, 0.0)),
    ]
    edges = [
        Edge(nodes[0], nodes[1]),
        Edge(nodes[1], nodes[2]),
    ]
    g = Graph(nodes=nodes, edges=edges)
    assert len(g.nodes) == 3
    assert len(g.edges) == 2


def test_edge_weight_label_offset_scales():
    a = Node("A", position=(-3.0, 0.0))
    b = Node("B", position=(3.0, 0.0))
    Edge(a, b, weight="5")


# ── PathHighlight ──────────────────────────────────────────────────────────────

def test_path_highlight_manual():
    nodes = [
        Node("A", position=(-2.0, 0.0)),
        Node("B", position=(0.0, 0.0)),
        Node("C", position=(2.0, 0.0)),
    ]
    edges = [
        Edge(nodes[0], nodes[1]),
        Edge(nodes[1], nodes[2]),
    ]
    g = Graph(nodes=nodes, edges=edges)
    ph = PathHighlight(g, ["A", "B", "C"])
    assert isinstance(ph, VGroup)
