"""Second chalk.graph demo -- breadth-first traversal on a hand-placed tree.

Run: uv run chalk chalk/examples/graph_demo2.py --scene BFSTraversalDemo -o out.mp4
"""
from chalk import (
    Scene,
    FadeIn,
    LaggedStart,
    MathTex,
    Circle,
    YELLOW,
    GREEN,
    GREY,
    SCALE_BODY,
    ZONE_BOTTOM,
    place_in_zone,
)
from chalk.graph import Node, Edge, Graph, PathHighlight
from chalk.layout import check_no_overlap


class BFSTraversalDemo(Scene):
    def construct(self):
        def build_tree() -> tuple[dict[str, Node], Graph]:
            nodes = {
                "S": Node("S", position=(0.0, 1.8)),
                "A": Node("A", position=(-2.4, 0.4)),
                "B": Node("B", position=(2.4, 0.4)),
                "C": Node("C", position=(-3.6, -1.4)),
                "D": Node("D", position=(-1.2, -1.4)),
                "E": Node("E", position=(1.2, -1.4)),
                "F": Node("F", position=(3.6, -1.4)),
            }
            check_no_overlap(list(nodes.values()), min_sep=1.5, raise_on_fail=True)
            graph = Graph(
                nodes=list(nodes.values()),
                edges=[
                    Edge(nodes["S"], nodes["A"], directed=False, color=GREY),
                    Edge(nodes["S"], nodes["B"], directed=False, color=GREY),
                    Edge(nodes["A"], nodes["C"], directed=False, color=GREY),
                    Edge(nodes["A"], nodes["D"], directed=False, color=GREY),
                    Edge(nodes["B"], nodes["E"], directed=False, color=GREY),
                    Edge(nodes["B"], nodes["F"], directed=False, color=GREY),
                ],
            )
            return nodes, graph

        def node_ring(node: Node) -> Circle:
            ring = Circle(radius=node.fitted_radius + 0.1, color=GREEN, stroke_width=3.0)
            ring.shift(float(node.position[0]), float(node.position[1]))
            return ring

        # -- Beat 1: tree structure ------------------------------------------
        nodes, tree = build_tree()
        title = MathTex(r"\mathrm{BFS\ starts\ at\ S}", color=GREY, scale=SCALE_BODY)
        place_in_zone(title, ZONE_BOTTOM)
        self.add(tree, title)
        self.play(FadeIn(tree, run_time=0.7), FadeIn(title, run_time=0.4))
        self.wait(1.1)
        self.clear()

        # -- Beat 2: level-order traversal -----------------------------------
        nodes, tree = build_tree()
        level0 = [node_ring(nodes["S"])]
        level1 = [node_ring(nodes["A"]), node_ring(nodes["B"])]
        level2 = [
            node_ring(nodes["C"]),
            node_ring(nodes["D"]),
            node_ring(nodes["E"]),
            node_ring(nodes["F"]),
        ]
        first_edges = [
            PathHighlight(tree, ["S", "A"], highlight_color=YELLOW),
            PathHighlight(tree, ["S", "B"], highlight_color=YELLOW),
        ]
        second_edges = [
            PathHighlight(tree, ["A", "C"], highlight_color=YELLOW),
            PathHighlight(tree, ["A", "D"], highlight_color=YELLOW),
            PathHighlight(tree, ["B", "E"], highlight_color=YELLOW),
            PathHighlight(tree, ["B", "F"], highlight_color=YELLOW),
        ]
        self.add(tree, *level0, *level1, *level2, *first_edges, *second_edges)
        self.play(FadeIn(tree, run_time=0.5))
        self.play(LaggedStart(*[FadeIn(ring, run_time=0.4) for ring in level0], lag_ratio=0.2))
        self.play(
            LaggedStart(
                *[FadeIn(edge, run_time=0.5) for edge in first_edges],
                *[FadeIn(ring, run_time=0.5) for ring in level1],
                lag_ratio=0.3,
            )
        )
        self.play(
            LaggedStart(
                *[FadeIn(edge, run_time=0.5) for edge in second_edges],
                *[FadeIn(ring, run_time=0.5) for ring in level2],
                lag_ratio=0.25,
            )
        )
        self.wait(0.5)
        self.clear()

        # -- Beat 3: final BFS order -----------------------------------------
        nodes, tree = build_tree()
        order = MathTex(
            r"S \to A \to B \to C \to D \to E \to F",
            color=YELLOW,
            scale=SCALE_BODY,
        )
        place_in_zone(order, ZONE_BOTTOM)
        rings = [node_ring(node) for node in nodes.values()]
        self.add(tree, *rings, order)
        self.play(
            FadeIn(tree, run_time=0.5),
            FadeIn(rings[0], run_time=0.4),
            LaggedStart(*[FadeIn(ring, run_time=0.4) for ring in rings[1:]], lag_ratio=0.15),
            FadeIn(order, run_time=0.6),
        )
        self.wait(2.0)
