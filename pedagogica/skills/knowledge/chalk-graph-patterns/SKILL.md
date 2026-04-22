---
name: chalk-graph-patterns
description: Hand-placement patterns for chalk Node/Edge/Graph scenes. Use when generating any scene with nodes and edges (graphs, state machines, Dijkstra, BFS traversal, dependency diagrams).
---

# Chalk Graph Patterns

## Rule

chalk.graph has NO auto-layout. Place every Node by hand. The from_adjacency method was removed — do not try to call it.

## Frame Constants

- FRAME 14.2 x 8.0
- SAFE_X ±6.6
- SAFE_Y ±3.5
- ZONE_TOP (2.0, 3.5)
- ZONE_CENTER (-2.0, 2.0)
- ZONE_BOTTOM (-3.5, -2.0)

## Node Widths Heuristic

- single-char label ≈ 0.7 units wide
- 2-char ≈ 1.0
- 4-char ≈ 1.4
- Fitted_radius grows with label.

## Minimum Pairwise Distance

Use 1.5 world units to avoid circle overlap. Use `chalk.layout.check_no_overlap(nodes, min_sep=1.5)` to verify at construction time.

## Grid Templates

Copy-paste these for typical graph sizes:

- 3 nodes linear: (-3, 0), (0, 0), (3, 0)
- 3 nodes triangle: (0, 1.5), (-1.5, -1), (1.5, -1)
- 4 nodes square: (-2, 1.5), (2, 1.5), (-2, -1.5), (2, -1.5)
- 5 nodes pentagon: (2.5*cos(theta), 2.5*sin(theta)) for theta in 90, 162, 234, 306, 18 degrees
- 6 nodes 3x2 grid: x ∈ {-3, 0, 3}, y ∈ {1.2, -1.2}
- 7+ nodes: split into two subfigures; do not pack one graph

## Edge Weight Label

Place with `next_to(edge_midpoint, 'UP', buff=0.25)`. Suppress label if the edge is shorter than 2.0 units.

## Full Example

```python
from chalk import Scene, FadeIn, MathTex, GREY, YELLOW
from chalk.graph import Node, Edge, Graph, PathHighlight
from chalk.layout import check_no_overlap


class DijkstraScene(Scene):
    def construct(self):
        node_map = {
            "S": Node("S", position=(-3.5, 1.0)),
            "A": Node("A", position=(-1.0, 1.0)),
            "B": Node("B", position=(-3.5, -1.5)),
            "C": Node("C", position=(1.5, 1.0)),
            "D": Node("D", position=(-1.0, -1.5)),
            "T": Node("T", position=(3.5, -1.5)),
        }
        nodes = list(node_map.values())
        check_no_overlap(nodes, min_sep=1.5)

        graph = Graph(
            nodes=nodes,
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
        highlight = PathHighlight(graph, ["S", "A", "D", "T"], highlight_color=YELLOW)
        title = MathTex(r"\mathrm{Shortest\ path:\ S \to A \to D \to T}", color=GREY)
        title.move_to(0.0, 3.0)

        self.add(title, graph, highlight)
        self.play(FadeIn(title), FadeIn(graph), FadeIn(highlight))
        self.wait(1.5)
```

## What NOT To Do

- Don't call Graph.from_adjacency.
- Don't call any _spring_layout or _tree_layout — they no longer exist.
- Don't pack 8+ labeled nodes into one graph.
