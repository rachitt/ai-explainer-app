"""chalk.graph demo — hand-placed Node, Edge, Graph, PathHighlight.

Run: uv run chalk chalk/examples/graph_demo.py --scene GraphDemo -o out.mp4
"""
from __future__ import annotations

import math

from chalk import Scene, FadeIn, YELLOW, GREY, MathTex
from chalk.graph import Node, Edge, Graph, PathHighlight


class GraphDemo(Scene):
    def construct(self):

        # ── Beat 1: linear chain ─────────────────────────────────────────────
        nodes1 = [
            Node("A", position=(-3.0, 0.0)),
            Node("B", position=(0.0, 0.0)),
            Node("C", position=(3.0, 0.0)),
        ]
        g1 = Graph(
            nodes=nodes1,
            edges=[
                Edge(nodes1[0], nodes1[1]),
                Edge(nodes1[1], nodes1[2]),
            ],
        )
        title1 = MathTex(r"\mathrm{Linear\ chain}", color=GREY, scale=0.7)
        title1.move_to(0.0, 3.0)
        self.add(title1, g1)
        self.play(FadeIn(title1, run_time=0.4), FadeIn(g1, run_time=0.7))
        self.wait(1.5)
        self.clear()

        # ── Beat 2: cycle ────────────────────────────────────────────────────
        labels2 = ["A", "B", "C", "D", "E"]
        angles = [90, 162, 234, 306, 18]
        nodes2 = [
            Node(
                label,
                position=(
                    2.0 * math.cos(math.radians(theta)),
                    2.0 * math.sin(math.radians(theta)),
                ),
            )
            for label, theta in zip(labels2, angles)
        ]
        g2 = Graph(
            nodes=nodes2,
            edges=[
                Edge(nodes2[i], nodes2[(i + 1) % len(nodes2)])
                for i in range(len(nodes2))
            ],
        )
        title2 = MathTex(r"\mathrm{Cycle}", color=GREY, scale=0.7)
        title2.move_to(0.0, 3.0)
        self.add(title2, g2)
        self.play(FadeIn(title2, run_time=0.4), FadeIn(g2, run_time=0.7))
        self.wait(1.5)
        self.clear()

        # ── Beat 3: grid ─────────────────────────────────────────────────────
        coords3 = [
            (-3.0, 1.2), (0.0, 1.2), (3.0, 1.2),
            (-3.0, -1.2), (0.0, -1.2), (3.0, -1.2),
        ]
        nodes3 = [Node(str(i + 1), position=coord) for i, coord in enumerate(coords3)]
        g3 = Graph(
            nodes=nodes3,
            edges=[
                Edge(nodes3[0], nodes3[1]),
                Edge(nodes3[1], nodes3[2]),
                Edge(nodes3[3], nodes3[4]),
                Edge(nodes3[4], nodes3[5]),
                Edge(nodes3[0], nodes3[3]),
                Edge(nodes3[1], nodes3[4]),
                Edge(nodes3[2], nodes3[5]),
            ],
        )
        title3 = MathTex(r"\mathrm{Grid}", color=GREY, scale=0.7)
        title3.move_to(0.0, 3.0)
        self.add(title3, g3)
        self.play(FadeIn(title3, run_time=0.4), FadeIn(g3, run_time=0.7))
        self.wait(1.5)
        self.clear()

        # ── Beat 4: shortest path ────────────────────────────────────────────
        node_map = {
            "S": Node("S", position=(-3.5, 1.0)),
            "A": Node("A", position=(-1.0, 1.0)),
            "B": Node("B", position=(-3.5, -1.5)),
            "C": Node("C", position=(1.5, 1.0)),
            "D": Node("D", position=(-1.0, -1.5)),
            "T": Node("T", position=(3.5, -1.5)),
        }
        nodes4 = list(node_map.values())
        g4 = Graph(
            nodes=nodes4,
            edges=[
                Edge(node_map["S"], node_map["A"], weight="2"),
                Edge(node_map["S"], node_map["B"], weight="4"),
                Edge(node_map["A"], node_map["C"], weight="3"),
                Edge(node_map["A"], node_map["D"], weight="1"),
                Edge(node_map["B"], node_map["D"], weight="2"),
                Edge(node_map["C"], node_map["T"], weight="5"),
                Edge(node_map["D"], node_map["T"], weight="3"),
            ],
        )
        ph = PathHighlight(g4, ["S", "A", "D", "T"])
        title4 = MathTex(
            r"\mathrm{Shortest\ path:\ S \to A \to D \to T}",
            color=YELLOW,
            scale=0.65,
        )
        title4.move_to(0.0, 3.0)
        self.add(title4, g4, ph)
        self.play(
            FadeIn(title4, run_time=0.4),
            FadeIn(g4, run_time=0.7),
            FadeIn(ph, run_time=0.7),
        )
        self.wait(1.5)
        self.clear()
