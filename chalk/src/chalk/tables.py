"""Table primitive for grid-aligned MathTex cells."""
from __future__ import annotations

from collections.abc import Sequence

from chalk.shapes import Line
from chalk.style import GREY, PRIMARY, SCALE_LABEL
from chalk.tex import MathTex
from chalk.vgroup import VGroup


class Table(VGroup):
    """Grid table with MathTex cells and Line borders."""

    def __init__(
        self,
        rows: Sequence[Sequence[str | None]],
        scale: float = SCALE_LABEL,
        pad_x: float = 0.25,
        pad_y: float = 0.18,
        color: str = GREY,
        stroke_width: float = 2.0,
        header_row: bool = False,
        cell_color: str = PRIMARY,
        cell_colors: Sequence[Sequence[str | None]] | None = None,
        col_align: str | Sequence[str] = "center",
    ) -> None:
        if len(rows) == 0:
            raise ValueError("Table needs at least one row")
        if len(rows[0]) == 0:
            raise ValueError("Table needs at least one column")

        self.n_rows = len(rows)
        self.n_cols = len(rows[0])

        for i, row in enumerate(rows):
            if len(row) != self.n_cols:
                raise ValueError(
                    f"row {i} has {len(row)} cells, expected {self.n_cols}"
                )

        if cell_colors is not None:
            if len(cell_colors) != self.n_rows:
                raise ValueError("cell_colors shape must match rows")
            for i, color_row in enumerate(cell_colors):
                if len(color_row) != self.n_cols:
                    raise ValueError(
                        f"cell_colors row {i} has {len(color_row)} cells, "
                        f"expected {self.n_cols}"
                    )

        alignments = _normalize_col_align(col_align, self.n_cols)

        self.cells: list[list[MathTex | None]] = []
        cell_widths: list[list[float]] = []
        cell_heights: list[list[float]] = []

        for r_idx, row in enumerate(rows):
            cell_row: list[MathTex | None] = []
            width_row: list[float] = []
            height_row: list[float] = []
            for c_idx, value in enumerate(row):
                if value is None:
                    cell_row.append(None)
                    width_row.append(0.0)
                    height_row.append(0.0)
                    continue

                tex_color = (
                    cell_colors[r_idx][c_idx]
                    if cell_colors is not None and cell_colors[r_idx][c_idx] is not None
                    else cell_color
                )
                cell = MathTex(value, color=tex_color, scale=scale)
                cell.color = tex_color
                xmin, ymin, xmax, ymax = cell.bbox()
                cell_row.append(cell)
                width_row.append(xmax - xmin)
                height_row.append(ymax - ymin)

            self.cells.append(cell_row)
            cell_widths.append(width_row)
            cell_heights.append(height_row)

        col_widths = [
            max(cell_widths[r][c] for r in range(self.n_rows)) + 2 * pad_x
            for c in range(self.n_cols)
        ]
        row_heights = [
            max(cell_heights[r]) + 2 * pad_y
            for r in range(self.n_rows)
        ]

        total_w = sum(col_widths)
        total_h = sum(row_heights)
        left = -total_w / 2
        top = total_h / 2

        x_edges = [left]
        for width in col_widths:
            x_edges.append(x_edges[-1] + width)

        y_edges = [top]
        for height in row_heights:
            y_edges.append(y_edges[-1] - height)

        submobjects = []

        if stroke_width != 0:
            for y in y_edges:
                submobjects.append(
                    Line(
                        (x_edges[0], y),
                        (x_edges[-1], y),
                        color=color,
                        stroke_width=stroke_width,
                    )
                )
            for x in x_edges:
                submobjects.append(
                    Line(
                        (x, y_edges[-1]),
                        (x, y_edges[0]),
                        color=color,
                        stroke_width=stroke_width,
                    )
                )
            if header_row:
                submobjects.append(
                    Line(
                        (x_edges[0], y_edges[1]),
                        (x_edges[-1], y_edges[1]),
                        color=color,
                        stroke_width=stroke_width * 1.5,
                    )
                )

        for r_idx, row in enumerate(self.cells):
            cell_center_y = (y_edges[r_idx] + y_edges[r_idx + 1]) / 2
            for c_idx, cell in enumerate(row):
                if cell is None:
                    continue
                cell_w = cell_widths[r_idx][c_idx]
                col_left = x_edges[c_idx]
                col_right = x_edges[c_idx + 1]
                if alignments[c_idx] == "left":
                    cell_center_x = col_left + pad_x + cell_w / 2
                elif alignments[c_idx] == "right":
                    cell_center_x = col_right - pad_x - cell_w / 2
                else:
                    cell_center_x = (col_left + col_right) / 2
                cell.move_to(cell_center_x, cell_center_y)
                submobjects.append(cell)

        super().__init__(*submobjects)


def _normalize_col_align(col_align: str | Sequence[str], n_cols: int) -> list[str]:
    valid = {"center", "left", "right"}
    if isinstance(col_align, str):
        alignments = [col_align] * n_cols
    else:
        if len(col_align) != n_cols:
            raise ValueError(f"col_align has {len(col_align)} entries, expected {n_cols}")
        alignments = list(col_align)

    for value in alignments:
        if value not in valid:
            raise ValueError(f"invalid col_align value: {value!r}")
    return alignments
