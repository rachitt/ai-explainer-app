"""Snapshot suite for C2 domain-kit demo keyframes.

Run normally:      uv run pytest chalk/tests/test_c2_demos_snapshot.py
Update baselines:  UPDATE_SNAPSHOTS=1 uv run pytest chalk/tests/test_c2_demos_snapshot.py
"""
import importlib.util
from pathlib import Path

import pytest

from chalk.testing import assert_snapshot

_EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def _load(filename: str, classname: str):
    """Load a scene class from a file in examples/."""
    path = _EXAMPLES_DIR / filename
    spec = importlib.util.spec_from_file_location(filename[:-3], path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return getattr(mod, classname)


# Each entry: (snapshot_name, demo_file, class_name, at_second)
_KEYFRAMES = [
    # Physics (duration ~10s, 3 beats)
    ("c2_physics_spring_mass", "physics_demo.py", "PhysicsDemo", 1.8),
    ("c2_physics_pendulum", "physics_demo.py", "PhysicsDemo", 5.0),
    ("c2_physics_freebody", "physics_demo.py", "PhysicsDemo", 8.8),
    # Circuits (duration ~12s, 3 beats)
    ("c2_circuits_gallery", "circuits_demo.py", "CircuitsDemo", 1.5),
    ("c2_circuits_currentflow", "circuits_demo.py", "CircuitsDemo", 4.0),
    ("c2_circuits_kirchhoff", "circuits_demo.py", "CircuitsDemo", 10.5),
    # Graph (duration ~11s, 4 beats)
    ("c2_graph_linear", "graph_demo.py", "GraphDemo", 2.0),
    ("c2_graph_pentagon", "graph_demo.py", "GraphDemo", 4.5),
    ("c2_graph_grid", "graph_demo.py", "GraphDemo", 7.0),
    ("c2_graph_dijkstra", "graph_demo.py", "GraphDemo", 10.0),
    # Chemistry (duration ~12s, 3 beats)
    ("c2_chem_atoms", "chemistry_demo.py", "ChemistryDemo", 2.0),
    ("c2_chem_co2", "chemistry_demo.py", "ChemistryDemo", 6.0),
    ("c2_chem_sn2", "chemistry_demo.py", "ChemistryDemo", 10.0),
    # Second examples
    ("c2_physics2_velocity", "physics_demo2.py", "ProjectileDemo", 1.5),
    ("c2_physics2_trajectory", "physics_demo2.py", "ProjectileDemo", 5.0),
    ("c2_physics2_apex_fbd", "physics_demo2.py", "ProjectileDemo", 8.0),
    ("c2_circuits2_loop", "circuits_demo2.py", "RCChargingDemo", 1.5),
    ("c2_circuits2_current", "circuits_demo2.py", "RCChargingDemo", 4.5),
    ("c2_circuits2_curve", "circuits_demo2.py", "RCChargingDemo", 8.0),
    ("c2_graph2_tree", "graph_demo2.py", "BFSTraversalDemo", 1.5),
    ("c2_graph2_bfs_mid", "graph_demo2.py", "BFSTraversalDemo", 4.5),
    ("c2_graph2_order", "graph_demo2.py", "BFSTraversalDemo", 8.0),
    ("c2_chem2_reactants", "chemistry_demo2.py", "AcidBaseDemo", 1.5),
    ("c2_chem2_arrow", "chemistry_demo2.py", "AcidBaseDemo", 4.5),
    ("c2_chem2_products", "chemistry_demo2.py", "AcidBaseDemo", 8.0),
]


@pytest.mark.parametrize(
    "name,filename,classname,at_sec",
    _KEYFRAMES,
    ids=[keyframe[0] for keyframe in _KEYFRAMES],
)
def test_c2_snapshot(name: str, filename: str, classname: str, at_sec: float):
    scene_cls = _load(filename, classname)
    assert_snapshot(scene_cls, at_sec, name, width=640, height=360, fps=30)
