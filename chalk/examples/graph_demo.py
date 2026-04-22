"""chalk.graph demo — Node, Edge, Graph, PathHighlight.

Beats:
1. Circular layout + fade in
2. Spring layout
3. Tree layout
4. Dijkstra-style path traversal highlight

Run: uv run chalk chalk/examples/graph_demo.py --scene GraphDemo -o out.mp4
"""
from chalk import (
    Scene, VGroup,
    FadeIn, FadeOut, Succession,
    PRIMARY, YELLOW, BLUE, GREEN, GREY,
    SCALE_LABEL, MathTex,
    next_to,
)
from chalk.graph import Node, Edge, Graph, PathHighlight


class GraphDemo(Scene):
    def construct(self):

        # ── Beat 1: circular layout ──────────────────────────────────────────
        adj_circle = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D", "E"],
            "D": ["E"],
            "E": [],
        }
        g_circ = Graph.from_adjacency(adj_circle, layout="circular", radius=2.2)
        title = MathTex(r"\mathrm{Circular\ layout}", color=GREY, scale=0.7)
        title.move_to(0.0, 3.3)
        self.add(title, g_circ)
        self.play(FadeIn(title, run_time=0.4), FadeIn(g_circ, run_time=0.7))
        self.wait(1.5)
        self.clear()

        # ── Beat 2: spring layout ────────────────────────────────────────────
        adj_spring = {
            "S": ["A", "B"],
            "A": ["C", "D"],
            "B": ["D", "E"],
            "C": [],
            "D": ["T"],
            "E": ["T"],
            "T": [],
        }
        g_spring = Graph.from_adjacency(adj_spring, layout="spring", radius=2.5)
        title2 = MathTex(r"\mathrm{Spring\ layout}", color=GREY, scale=0.7)
        title2.move_to(0.0, 3.3)
        self.add(title2, g_spring)
        self.play(FadeIn(title2, run_time=0.4), FadeIn(g_spring, run_time=0.7))
        self.wait(1.5)
        self.clear()

        # ── Beat 3: tree layout ──────────────────────────────────────────────
        adj_tree = {
            "root": ["L", "R"],
            "L": ["LL", "LR"],
            "R": ["RL", "RR"],
            "LL": [], "LR": [], "RL": [], "RR": [],
        }
        g_tree = Graph.from_adjacency(adj_tree, layout="tree", radius=2.5)
        title3 = MathTex(r"\mathrm{Tree\ layout}", color=GREY, scale=0.7)
        title3.move_to(0.0, 3.3)
        self.add(title3, g_tree)
        self.play(FadeIn(title3, run_time=0.4), FadeIn(g_tree, run_time=0.7))
        self.wait(1.5)
        self.clear()

        # ── Beat 4: path traversal highlight ────────────────────────────────
        adj_path = {
            "S": [("A", "2"), ("B", "4")],
            "A": [("C", "3"), ("D", "1")],
            "B": [("D", "2")],
            "C": [("T", "5")],
            "D": [("T", "3")],
            "T": [],
        }
        g_path = Graph.from_adjacency(adj_path, layout="spring", radius=2.0,
                                      directed=True, edge_color=GREY)
        ph = PathHighlight(g_path, ["S", "A", "D", "T"])
        title4 = MathTex(r"\mathrm{Shortest\ path:\ S \to A \to D \to T}",
                         color=YELLOW, scale=0.65)
        title4.move_to(0.0, 3.3)
        self.add(title4, g_path)
        self.play(FadeIn(title4, run_time=0.4), FadeIn(g_path, run_time=0.7))
        self.add(ph)
        self.play(FadeIn(ph, run_time=0.8))
        self.wait(2.0)
        self.clear()
