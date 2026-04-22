"""Regression suite — 10 Phase-1 calculus topics rendered on chalk.

Run normally:      uv run pytest chalk/tests/test_calculus_regression.py
Update baselines:  UPDATE_SNAPSHOTS=1 uv run pytest chalk/tests/test_calculus_regression.py
"""
import importlib.util
from pathlib import Path

import pytest

from chalk.testing import snapshot, assert_snapshot

_SCENES_DIR = Path(__file__).parent / "regression"


def _load_class(filename: str, classname: str):
    """Load a scene class from a file in the regression/ directory."""
    path = _SCENES_DIR / filename
    spec = importlib.util.spec_from_file_location(filename[:-3], path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return getattr(mod, classname)


_TOPICS = [
    ("topic_01_derivative_rate",   "topic_01_derivative_rate.py",   "DerivativeAsRate",    1.5),
    ("topic_02_derivative_slope",  "topic_02_derivative_slope.py",  "DerivativeAsSlope",   1.5),
    ("topic_03_chain_rule",        "topic_03_chain_rule.py",        "ChainRuleBoxes",      2.0),
    ("topic_04_product_rule",      "topic_04_product_rule.py",      "ProductRuleBox",      2.0),
    ("topic_05_riemann_integral",  "topic_05_riemann_integral.py",  "RiemannToIntegral",   3.0),
    ("topic_06_ftc",               "topic_06_ftc.py",               "FTCAccumulator",      2.0),
    ("topic_07_epsilon_delta",     "topic_07_epsilon_delta.py",     "EpsilonDelta",        2.0),
    ("topic_08_related_rates",     "topic_08_related_rates.py",     "RelatedRatesBalloon", 2.0),
    ("topic_09_optimization",      "topic_09_optimization.py",      "Optimization",        2.0),
    ("topic_10_area_between",      "topic_10_area_between.py",      "AreaBetweenCurves",   2.0),
]


def _topic_params():
    for name, filename, classname, at_sec in _TOPICS:
        scene_cls = _load_class(filename, classname)
        yield pytest.param(name, scene_cls, at_sec, id=name)


@pytest.mark.parametrize("name,scene_cls,at_sec", list(_topic_params()))
def test_topic_renders(name, scene_cls, at_sec):
    """Each topic must render a non-trivial frame at the given second."""
    frame = snapshot(scene_cls, at_second=at_sec, width=640, height=360, fps=30)
    assert frame is not None
    assert frame.shape == (360, 640, 4)
    assert frame.sum() > 0, f"{name}: frame is all black — scene likely crashed"


@pytest.mark.parametrize("name,scene_cls,at_sec", list(_topic_params()))
def test_topic_snapshot(name, scene_cls, at_sec):
    """Snapshot-diff: compare frame against committed baseline PNG.

    First run (UPDATE_SNAPSHOTS=1) writes baselines; subsequent runs compare.
    """
    assert_snapshot(scene_cls, at_sec, f"regression_{name}",
                    width=640, height=360, fps=30)
