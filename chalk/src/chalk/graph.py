"""chalk.graph — domain primitive kit for graph/network scenes.

Pure compositions of C1 primitives. No new renderer features.

Exports: Node, Edge, Graph, PathHighlight
"""
from __future__ import annotations

import numpy as np

from chalk.vgroup import VGroup
from chalk.style import PRIMARY, YELLOW, BLUE, GREEN, GREY, SCALE_LABEL, SCALE_ANNOT
from chalk.connectable import circle_edge_toward, resolve_endpoint


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

        lbl = MathTex(label, color=color, scale=SCALE_LABEL)
        xmin, ymin, xmax, ymax = lbl.bbox()
        label_hw = (xmax - xmin) / 2
        label_hh = (ymax - ymin) / 2
        self.fitted_radius = max(radius, max(label_hw, label_hh) + 0.12)

        self._label = label
        self.position = np.array(position, dtype=float)
        circle = Circle(
            radius=self.fitted_radius,
            color=color,
            fill_color=color,
            fill_opacity=0.25,
            stroke_width=2.5,
        )
        circle.shift(position[0], position[1])
        lbl.move_to(position[0], position[1])

        super().__init__(circle, lbl)

    @property
    def center(self) -> tuple[float, float]:
        return (float(self.position[0]), float(self.position[1]))

    def edge_toward(self, target: tuple[float, float]) -> tuple[float, float]:
        return circle_edge_toward(
            float(self.position[0]),
            float(self.position[1]),
            self.fitted_radius,
            target,
        )


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

        pa = np.array(a.center, dtype=float)
        pb = np.array(b.center, dtype=float)
        start = np.array(resolve_endpoint(a, b.center), dtype=float)
        end = np.array(resolve_endpoint(b, a.center), dtype=float)
        chord = pb - pa
        dist = float(np.linalg.norm(chord))

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
            ra = a.fitted_radius
            rb = b.fitted_radius
            min_label_edge = ra + rb + 0.6  # need room for label between node borders
            if dist < min_label_edge:
                pass  # skip weight label, edge too short
            else:
                mid = (pa + pb) / 2
                # Offset label slightly perpendicular to edge
                perp = np.array([-chord[1], chord[0]])
                if np.linalg.norm(perp) > 1e-9:
                    perp = perp / np.linalg.norm(perp)
                lbl_offset = max(0.3, 0.15 * dist)
                lbl_pos = mid + lbl_offset * perp
                wlbl = MathTex(weight, color=color, scale=SCALE_ANNOT)
                wlbl.move_to(float(lbl_pos[0]), float(lbl_pos[1]))
                mobs.append(wlbl)

        super().__init__(*mobs)


class Graph(VGroup):
    """Assembled graph from nodes and edges.

    Built directly from Node/Edge lists.
    """

    def __init__(
        self,
        nodes: list[Node],
        edges: list[Edge],
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        super().__init__(*edges, *nodes)  # edges drawn first (behind nodes)


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
            ring = Circle(
                radius=node.fitted_radius + 0.1,
                color=node_highlight_color,
                stroke_width=3.5,
            )
            ring.shift(float(node.position[0]), float(node.position[1]))
            mobs.append(ring)

            if prev is not None:
                pa = prev.position
                pb = node.position
                chord = pb - pa
                dist = float(np.linalg.norm(chord))
                ra = prev.fitted_radius
                rb = node.fitted_radius
                if dist > ra + rb + 0.1:
                    u = chord / dist
                    start = pa + ra * u
                    end = pb - rb * u
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
