"""chalk.graph — domain primitive kit for graph/network scenes.

Pure compositions of C1 primitives. No new renderer features.

Exports: Node, Edge, Graph, PathHighlight
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from chalk.vgroup import VGroup
from chalk.style import PRIMARY, YELLOW, BLUE, GREEN, GREY, SCALE_LABEL, SCALE_ANNOT


class Node(VGroup):
    """Labeled circle representing a graph node."""

    def __init__(
        self,
        label: str,
        position: tuple[float, float] = (0.0, 0.0),
        radius: float = 0.35,
        color: str = BLUE,
    ) -> None:
        from chalk.shapes import Circle
        from chalk.tex import MathTex

        self._label = label
        self.position = np.array(position, dtype=float)
        circle = Circle(radius=radius, color=color, fill_color=color, fill_opacity=0.25,
                        stroke_width=2.5)
        circle.shift(position[0], position[1])
        lbl = MathTex(label, color=color, scale=SCALE_LABEL)
        lbl.move_to(position[0], position[1])

        super().__init__(circle, lbl)


class Edge(VGroup):
    """Arrow or line between two Nodes.

    directed=True → Arrow; directed=False → Line.
    weight label is drawn at the midpoint if provided.
    """

    def __init__(
        self,
        a: Node,
        b: Node,
        weight: str = "",
        directed: bool = True,
        color: str = GREY,
        stroke_width: float = 2.0,
    ) -> None:
        from chalk.shapes import Arrow, Line

        pa = a.position
        pb = b.position
        chord = pb - pa
        dist = float(np.linalg.norm(chord))

        # Shorten endpoints so arrow tips don't overlap node circles
        node_r = 0.35
        if dist > 2 * node_r + 1e-9:
            u = chord / dist
            start = pa + node_r * u
            end = pb - node_r * u
        else:
            start, end = pa, pb

        mobs: list = []
        if directed:
            mobs.append(Arrow(
                (float(start[0]), float(start[1])),
                (float(end[0]), float(end[1])),
                color=color, stroke_width=stroke_width,
                head_length=0.2, head_width=0.15, shaft_width=0.04,
            ))
        else:
            mobs.append(Line(
                (float(start[0]), float(start[1])),
                (float(end[0]), float(end[1])),
                color=color, stroke_width=stroke_width,
            ))

        if weight:
            from chalk.tex import MathTex
            mid = (pa + pb) / 2
            # Offset label slightly perpendicular to edge
            perp = np.array([-chord[1], chord[0]])
            if np.linalg.norm(perp) > 1e-9:
                perp = perp / np.linalg.norm(perp)
            lbl_pos = mid + 0.3 * perp
            wlbl = MathTex(weight, color=color, scale=SCALE_ANNOT)
            wlbl.move_to(float(lbl_pos[0]), float(lbl_pos[1]))
            mobs.append(wlbl)

        super().__init__(*mobs)


class Graph(VGroup):
    """Assembled graph from nodes and edges.

    Built via Graph.from_adjacency() or directly from Node/Edge lists.
    """

    def __init__(
        self,
        nodes: list[Node],
        edges: list[Edge],
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        super().__init__(*edges, *nodes)  # edges drawn first (behind nodes)

    @classmethod
    def from_adjacency(
        cls,
        adj: dict[str, list[str | tuple[str, str]]],
        layout: str = "circular",
        radius: float = 2.5,
        directed: bool = True,
        node_color: str = BLUE,
        edge_color: str = GREY,
    ) -> "Graph":
        """Build a Graph from an adjacency dict.

        adj maps node label → list of neighbor labels (or (neighbor, weight) tuples).

        Layouts:
          "circular" — nodes on a circle of given radius.
          "spring"   — force-directed layout (Fruchterman-Reingold, 200 iterations).
          "tree"     — top-down tree layout (BFS from first node).
        """
        node_labels = list(adj.keys())
        # Collect all labels (some may appear only as neighbors)
        all_labels: list[str] = list(dict.fromkeys(
            node_labels + [
                nb if isinstance(nb, str) else nb[0]
                for neighbors in adj.values()
                for nb in neighbors
            ]
        ))

        positions = _compute_layout(all_labels, adj, layout, radius)
        node_map: dict[str, Node] = {
            label: Node(label, position=positions[label], color=node_color)
            for label in all_labels
        }

        edges: list[Edge] = []
        for src, neighbors in adj.items():
            for nb in neighbors:
                if isinstance(nb, tuple):
                    dst, weight = nb[0], nb[1]
                else:
                    dst, weight = nb, ""
                if dst in node_map:
                    edges.append(Edge(
                        node_map[src], node_map[dst],
                        weight=str(weight), directed=directed, color=edge_color,
                    ))

        return cls(nodes=list(node_map.values()), edges=edges)


def _compute_layout(
    labels: list[str],
    adj: dict[str, list[Any]],
    layout: str,
    radius: float,
) -> dict[str, tuple[float, float]]:
    n = len(labels)
    if n == 0:
        return {}

    if layout == "circular":
        return {
            label: (radius * math.cos(2 * math.pi * i / n),
                    radius * math.sin(2 * math.pi * i / n))
            for i, label in enumerate(labels)
        }

    if layout == "spring":
        return _spring_layout(labels, adj, radius)

    if layout == "tree":
        return _tree_layout(labels, adj, radius)

    # Fallback to circular
    return _compute_layout(labels, adj, "circular", radius)


def _spring_layout(
    labels: list[str],
    adj: dict[str, list[Any]],
    radius: float,
    iterations: int = 200,
) -> dict[str, tuple[float, float]]:
    """Fruchterman-Reingold force-directed layout."""
    n = len(labels)
    idx = {label: i for i, label in enumerate(labels)}

    # Init on a circle
    pos = np.array([
        [radius * math.cos(2 * math.pi * i / n), radius * math.sin(2 * math.pi * i / n)]
        for i in range(n)
    ], dtype=float)

    area = (2 * radius) ** 2
    k = math.sqrt(area / max(n, 1))
    t = radius * 0.5  # initial temperature

    for _ in range(iterations):
        disp = np.zeros((n, 2))

        # Repulsive forces between all pairs
        for i in range(n):
            for j in range(i + 1, n):
                delta = pos[i] - pos[j]
                d = float(np.linalg.norm(delta))
                if d < 1e-6:
                    delta = np.random.randn(2)
                    d = float(np.linalg.norm(delta))
                force = k * k / d
                unit = delta / d
                disp[i] += force * unit
                disp[j] -= force * unit

        # Attractive forces along edges
        for src, neighbors in adj.items():
            if src not in idx:
                continue
            i = idx[src]
            for nb in neighbors:
                dst = nb if isinstance(nb, str) else nb[0]
                if dst not in idx:
                    continue
                j = idx[dst]
                delta = pos[i] - pos[j]
                d = float(np.linalg.norm(delta))
                if d < 1e-6:
                    continue
                force = d * d / k
                unit = delta / d
                disp[i] -= force * unit
                disp[j] += force * unit

        # Apply displacement with temperature cap
        for i in range(n):
            d = float(np.linalg.norm(disp[i]))
            if d > 1e-9:
                pos[i] += disp[i] / d * min(d, t)

        t *= 0.95  # cool down

    # Center and scale to fit within radius
    center = pos.mean(axis=0)
    pos -= center
    max_dist = float(np.linalg.norm(pos, axis=1).max())
    if max_dist > 1e-9:
        pos *= radius / max_dist

    return {label: (float(pos[i, 0]), float(pos[i, 1])) for i, label in enumerate(labels)}


def _tree_layout(
    labels: list[str],
    adj: dict[str, list[Any]],
    radius: float,
) -> dict[str, tuple[float, float]]:
    """BFS-based top-down tree layout."""
    if not labels:
        return {}

    root = labels[0]
    # BFS to determine levels
    levels: dict[str, int] = {root: 0}
    order = [root]
    queue = [root]
    visited = {root}

    while queue:
        node = queue.pop(0)
        for nb in adj.get(node, []):
            dst = nb if isinstance(nb, str) else nb[0]
            if dst not in visited:
                visited.add(dst)
                levels[dst] = levels[node] + 1
                queue.append(dst)
                order.append(dst)

    # Assign all remaining labels level 0 (disconnected)
    for label in labels:
        if label not in levels:
            levels[label] = 0

    max_level = max(levels.values()) if levels else 0
    level_y = {lvl: -lvl * radius / max(max_level, 1) for lvl in range(max_level + 1)}

    # Group by level, assign x positions
    from collections import defaultdict
    level_nodes: dict[int, list[str]] = defaultdict(list)
    for label in order:
        level_nodes[levels[label]].append(label)
    for label in labels:
        if label not in levels:
            level_nodes[0].append(label)

    positions: dict[str, tuple[float, float]] = {}
    for lvl, nodes_at_lvl in level_nodes.items():
        n = len(nodes_at_lvl)
        for i, label in enumerate(nodes_at_lvl):
            x = (i - (n - 1) / 2) * radius / max(max_level, 1) * 1.5
            positions[label] = (x, level_y.get(lvl, 0.0))

    return positions


class PathHighlight(VGroup):
    """Animated traversal path overlay on a Graph.

    Highlights a sequence of nodes and the edges between them in order,
    using Succession to reveal each step.

    Use as: self.play(PathHighlight(graph, ["A", "B", "C"]).animate())
    But since we build statically, PathHighlight is just the highlighted VGroup;
    the caller uses FadeIn or Write to reveal it.
    """

    def __init__(
        self,
        graph: Graph,
        node_sequence: list[str],
        highlight_color: str = YELLOW,
        node_highlight_color: str = GREEN,
    ) -> None:
        from chalk.shapes import Circle
        from chalk.shapes import Arrow

        node_map = {
            # Try to extract label from Node's second submobject (MathTex)
            # Label is whatever label was passed to Node()
            _node_label(n): n
            for n in graph.nodes
        }

        mobs: list = []
        prev: Node | None = None
        for label in node_sequence:
            node = node_map.get(label)
            if node is None:
                continue
            # Highlight ring around node
            ring = Circle(radius=0.45, color=node_highlight_color, stroke_width=3.5)
            ring.shift(float(node.position[0]), float(node.position[1]))
            mobs.append(ring)

            if prev is not None:
                pa = prev.position
                pb = node.position
                chord = pb - pa
                dist = float(np.linalg.norm(chord))
                node_r = 0.35
                if dist > 2 * node_r:
                    u = chord / dist
                    start = pa + node_r * u
                    end = pb - node_r * u
                    mobs.append(Arrow(
                        (float(start[0]), float(start[1])),
                        (float(end[0]), float(end[1])),
                        color=highlight_color, stroke_width=3.0,
                        head_length=0.22, head_width=0.18, shaft_width=0.055,
                    ))
            prev = node

        super().__init__(*mobs)


def _node_label(node: Node) -> str:
    return getattr(node, "_label", "")
