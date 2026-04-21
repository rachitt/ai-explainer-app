import math

import numpy as np
import pytest

from chalk import (
    Rectangle, Arrow, Axes, plot_function,
    BLUE,
)


def test_rectangle_points_shape():
    r = Rectangle(width=4.0, height=2.0)
    assert r.points.shape == (64, 2)
    # Centered at origin
    xmin, xmax = r.points[:, 0].min(), r.points[:, 0].max()
    ymin, ymax = r.points[:, 1].min(), r.points[:, 1].max()
    assert abs((xmin + xmax) / 2) < 1e-6
    assert abs((ymin + ymax) / 2) < 1e-6
    assert abs(xmax - xmin - 4.0) < 1e-6
    assert abs(ymax - ymin - 2.0) < 1e-6


def test_rectangle_interpolates_with_square():
    from chalk import Square
    r = Rectangle(width=3.0, height=1.0)
    s = Square(side=1.0)
    # Same N points means interpolate() won't need subdivide
    r.interpolate(s, 0.5)
    assert r.points.shape == (64, 2)


def test_arrow_points_and_direction():
    a = Arrow((0.0, 0.0), (2.0, 0.0), head_length=0.3, head_width=0.2, shaft_width=0.06)
    # Closed 7-vertex polygon → 7 * 4 = 28 points
    assert a.points.shape == (28, 2)
    # Arrow tip should appear in the points (x = 2.0)
    assert np.any(np.isclose(a.points[:, 0], 2.0, atol=1e-6))
    # Points should lie within bounds roughly [0, 2] x [-0.15, 0.15]
    assert a.points[:, 0].min() > -1e-6
    assert a.points[:, 0].max() <= 2.0 + 1e-6
    assert a.points[:, 1].max() <= 0.2
    assert a.points[:, 1].min() >= -0.2


def test_arrow_diagonal_has_correct_endpoints():
    a = Arrow((1.0, 1.0), (3.0, 2.0))
    # Tip of the arrow should be exactly at end
    tip_matches = np.isclose(a.points, np.array([3.0, 2.0]), atol=1e-6).all(axis=1)
    assert tip_matches.any()


def test_arrow_zero_length_doesnt_crash():
    a = Arrow((0.5, 0.5), (0.5, 0.5))
    # Degenerate; should still produce a points array
    assert a.points.shape[1] == 2


def test_axes_origin_mapping():
    ax = Axes(x_range=(-5, 5), y_range=(-3, 3), width=10, height=6)
    assert ax.to_point(0.0, 0.0) == (0.0, 0.0)
    assert ax.to_point(5.0, 3.0) == (5.0, 3.0)
    assert ax.to_point(-5.0, -3.0) == (-5.0, -3.0)


def test_axes_contains_axis_and_ticks():
    ax = Axes(x_range=(-2, 2), y_range=(-1, 1), width=4, height=2,
              x_step=1.0, y_step=0.5)
    # 2 main axes + 3 x-ticks at {-2,-1,1,2} minus skipped 0 = 4 x-ticks
    # + 3 y-ticks at {-1,-0.5,0.5,1} minus 0 = 4 y-ticks
    # Total ≥ 2 + 4 + 4 = 10
    assert len(ax) >= 10


def test_plot_function_parabola_points():
    ax = Axes(x_range=(-2, 2), y_range=(0, 4), width=4, height=4)
    curve = plot_function(ax, lambda x: x * x,
                          x_start=-2, x_end=2, resolution=20, color=BLUE)
    # 20 segments × 4 points per cubic = 80 points
    assert curve.points.shape == (80, 2)
    # y=x² is non-negative, so curve points should have y >= bottom of axes
    y_bottom = -2.0  # height=4, centered at origin, bottom at y=-2 in world
    assert curve.points[:, 1].min() >= y_bottom - 1e-6


def test_plot_function_sine_wave():
    ax = Axes(x_range=(-math.pi, math.pi), y_range=(-1.2, 1.2),
              width=8, height=4)
    curve = plot_function(ax, math.sin, resolution=40, color=BLUE)
    assert curve.points.shape == (160, 2)
    # Max y and min y of sin over [-π, π] should map near the top and bottom
    assert curve.points[:, 1].max() > 1.5
    assert curve.points[:, 1].min() < -1.5
