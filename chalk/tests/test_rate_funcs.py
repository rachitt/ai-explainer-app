import numpy as np
from chalk.rate_funcs import linear, smooth, ease_in_out


def test_linear_endpoints():
    assert linear(0.0) == 0.0
    assert linear(1.0) == 1.0


def test_smooth_endpoints():
    assert smooth(0.0) == 0.0
    assert smooth(1.0) == 1.0


def test_smooth_midpoint():
    assert smooth(0.5) == pytest_approx(0.5)


def test_ease_in_out_endpoints():
    assert ease_in_out(0.0) == 0.0
    assert ease_in_out(1.0) == 1.0


def test_smooth_monotonic():
    ts = np.linspace(0, 1, 100)
    vals = [smooth(t) for t in ts]
    assert all(vals[i] <= vals[i + 1] for i in range(len(vals) - 1))


def pytest_approx(val: float, abs: float = 1e-9):
    import pytest
    return pytest.approx(val, abs=abs)
