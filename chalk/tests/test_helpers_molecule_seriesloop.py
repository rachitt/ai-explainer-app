import pytest
from chalk.chemistry import Molecule
from chalk.circuits import Resistor, SeriesLoop, Wire


def test_molecule_caption_gap():
    mol = Molecule(
        atoms=[
            {"symbol": "C", "position": (0.0, 0.0)},
            {"symbol": "O", "position": (1.2, 0.0)},
        ],
        bonds=[{"a": 0, "b": 1, "order": 2}],
        caption=r"\mathrm{CO}_2",
        caption_buff=0.45,
    )
    _lx0, ly0, _lx1, _ly1 = mol._layout.bbox()
    _cx0, _cy0, _cx1, cy1 = mol._caption.bbox()
    assert cy1 < ly0 - (0.45 - 0.15), f"caption top {cy1} too close to mol bottom {ly0}"


def test_seriesloop_wire_breaks():
    r1 = Resistor((-3.0, 1.5), (-1.0, 1.5))
    r2 = Resistor((1.0, 1.5), (3.0, 1.5))
    loop = SeriesLoop([r1, r2], width=8.0, height=3.0)
    wires = [c for c in loop.submobjects if isinstance(c, Wire)]
    assert len(wires) == 1


def test_seriesloop_n_gt_4_raises():
    comps = [Resistor((0.0, 0.0), (0.5, 0.0)) for _ in range(5)]
    with pytest.raises(NotImplementedError):
        SeriesLoop(comps)
