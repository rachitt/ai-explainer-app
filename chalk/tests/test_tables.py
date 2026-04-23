from __future__ import annotations

import shutil

import pytest

from chalk import Line, MathTex, Table
from chalk.layout import check_bbox_overlap


def _line_children(table: Table) -> list[Line]:
    return [m for m in table.submobjects if isinstance(m, Line)]


def _mathtex_children(table: Table) -> list[MathTex]:
    return [m for m in table.submobjects if isinstance(m, MathTex)]


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not found")
def test_basic_2x3_table_builds():
    table = Table([["a", "b", "c"], ["d", "e", "f"]])

    assert table.n_rows == 2
    assert table.n_cols == 3
    assert sum(cell is not None for row in table.cells for cell in row) == 6
    lines = _line_children(table)
    horizontal = [line for line in lines if line.points[0][1] == line.points[-1][1]]
    table_xmin, _, table_xmax, _ = table.bbox()
    internal_vertical = [
        line
        for line in lines
        if line.points[0][0] == line.points[-1][0]
        and table_xmin < line.points[0][0] < table_xmax
    ]
    assert len(horizontal) >= 2
    assert len(internal_vertical) >= 1


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not found")
def test_none_cell_blank():
    table = Table([["a", None], ["b", "c"]])

    assert table.cells[0][1] is None
    assert len(_line_children(table)) > 0


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not found")
def test_header_row_adds_double_line():
    plain = Table([["a", "b"], ["c", "d"]], stroke_width=2.0)
    header = Table([["a", "b"], ["c", "d"]], stroke_width=2.0, header_row=True)

    assert len(_line_children(header)) == len(_line_children(plain)) + 1
    assert any(line.stroke_width == 3.0 for line in _line_children(header))


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not found")
def test_stroke_width_zero_suppresses_borders():
    table = Table([["a", "b"]], stroke_width=0)

    assert len(_line_children(table)) == 0
    assert len(_mathtex_children(table)) >= 1


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not found")
def test_col_align_left_vs_center_positions_text_differently():
    table = Table([["x", "wide"], ["wideword", "x"]], col_align=["left", "center"])

    left_cell = table.cells[0][0]
    center_cell = table.cells[0][1]
    assert left_cell is not None
    assert center_cell is not None
    left_x = (left_cell.bbox()[0] + left_cell.bbox()[2]) / 2
    center_x = (center_cell.bbox()[0] + center_cell.bbox()[2]) / 2
    table_xmin, _, table_xmax, _ = table.bbox()
    col_width = (table_xmax - table_xmin) / 2
    left_offset = left_x - (table_xmin + col_width / 2)
    center_offset = center_x - (table_xmin + col_width + col_width / 2)
    assert left_offset != pytest.approx(center_offset)


def test_ragged_rows_raise():
    with pytest.raises(ValueError, match="row.*expected"):
        Table([["a", "b"], ["c"]])


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not found")
def test_cell_colors_per_cell_override():
    table = Table(
        [["a", "b"], ["c", "d"]],
        cell_color="#00FF00",
        cell_colors=[[None, "#FF0000"], [None, None]],
    )

    assert table.cells[0][1] is not None
    assert table.cells[0][1].color == "#FF0000"
    assert table.cells[0][0] is not None
    assert table.cells[0][0].color == "#00FF00"
    assert table.cells[1][0] is not None
    assert table.cells[1][0].color == "#00FF00"


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not found")
def test_move_to_positions_center():
    table = Table([["a", "b"], ["c", "d"]])
    table.move_to(2.0, 1.0)
    xmin, ymin, xmax, ymax = table.bbox()

    assert (xmin + xmax) / 2 == pytest.approx(2.0, abs=0.01)
    assert (ymin + ymax) / 2 == pytest.approx(1.0, abs=0.01)


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not found")
def test_table_bbox_recurses_through_cells():
    table = Table([["a"]], stroke_width=0)
    xmin, ymin, xmax, ymax = table.bbox()

    assert xmax - xmin > 0
    assert ymax - ymin > 0


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not found")
def test_two_tables_nonoverlapping_when_spaced():
    t1 = Table([["a"]])
    t2 = Table([["b"]])
    t1.shift(-3.0, 0.0)
    t2.shift(3.0, 0.0)

    assert len(check_bbox_overlap([t1, t2], padding=0.0)) == 0
