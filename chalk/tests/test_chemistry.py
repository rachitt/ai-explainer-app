"""Tests for chalk.chemistry: Atom, Bond, MoleculeLayout, ReactionArrow."""
from __future__ import annotations

import pytest
from chalk.chemistry import Atom, Bond, MoleculeLayout, ReactionArrow
from chalk.vgroup import VGroup
from chalk.scene import Scene
from chalk.animation import FadeIn
from chalk.camera import Camera2D


class _NullSink:
    def write(self, _): pass


def _attach(scene):
    cam = Camera2D()
    cam.pixel_width = 320
    cam.pixel_height = 180
    scene._attach(_NullSink(), camera=cam)


# ── Atom ─────────────────────────────────────────────────────────────────────

def test_atom_is_vgroup():
    a = Atom("C")
    assert isinstance(a, VGroup)


def test_atom_no_charge():
    a = Atom("O")
    # circle + symbol label
    assert len(a.submobjects) == 2


def test_atom_with_charge():
    a = Atom("N", charge="+")
    # circle + symbol + charge label
    assert len(a.submobjects) == 3


def test_atom_position():
    a = Atom("C", position=(2.0, -1.0))
    import numpy as np
    assert a.position == pytest.approx([2.0, -1.0])


def test_atom_renders():
    class AScene(Scene):
        def construct(self):
            a = Atom("C", position=(0.0, 0.0))
            self.add(a)
            self.play(FadeIn(a, run_time=0.3))
            self.wait(0.2)
    scene = AScene()
    _attach(scene)
    scene.construct()


# ── Bond ─────────────────────────────────────────────────────────────────────

def test_bond_single():
    b = Bond((0.0, 0.0), (1.5, 0.0), order=1)
    assert isinstance(b, VGroup)
    assert len(b.submobjects) == 1  # one Line


def test_bond_double():
    b = Bond((0.0, 0.0), (1.5, 0.0), order=2)
    # two offset lines
    assert len(b.submobjects) == 2


def test_bond_triple():
    b = Bond((0.0, 0.0), (1.5, 0.0), order=3)
    # two offset lines + center line = 3
    assert len(b.submobjects) == 3


def test_bond_wedge():
    b = Bond((0.0, 0.0), (1.5, 0.0), stereo="wedge")
    assert len(b.submobjects) == 1  # filled triangle Polygon


def test_bond_dash():
    b = Bond((0.0, 0.0), (1.5, 0.0), stereo="dash")
    # 6 short perpendicular lines
    assert len(b.submobjects) == 6


def test_bond_zero_length_safe():
    b = Bond((0.0, 0.0), (0.0, 0.0))
    assert isinstance(b, VGroup)
    assert len(b.submobjects) == 0


def test_bond_renders():
    class BScene(Scene):
        def construct(self):
            b = Bond((-1.0, 0.0), (1.0, 0.0), order=2)
            self.add(b)
            self.play(FadeIn(b, run_time=0.3))
            self.wait(0.2)
    scene = BScene()
    _attach(scene)
    scene.construct()


# ── MoleculeLayout ────────────────────────────────────────────────────────────

def test_molecule_from_atoms_bonds():
    atoms = [
        {"symbol": "C", "position": (0.0, 0.0)},
        {"symbol": "O", "position": (1.5, 0.0)},
    ]
    bonds = [{"a": 0, "b": 1, "order": 2}]
    mol = MoleculeLayout.from_atoms_bonds(atoms, bonds)
    assert isinstance(mol, VGroup)
    assert len(mol.atoms) == 2
    assert len(mol.bonds) == 1


def test_molecule_from_atoms_bonds_renders():
    atoms = [
        {"symbol": "C", "position": (-0.75, 0.0)},
        {"symbol": "O", "position": (0.75, 0.0)},
    ]
    bonds = [{"a": 0, "b": 1, "order": 2}]
    mol = MoleculeLayout.from_atoms_bonds(atoms, bonds)

    class MScene(Scene):
        def construct(self):
            self.add(mol)
            self.play(FadeIn(mol, run_time=0.3))
            self.wait(0.2)
    scene = MScene()
    _attach(scene)
    scene.construct()


def test_molecule_from_smiles_no_rdkit():
    """Without RDKit installed, from_smiles returns a placeholder gracefully."""
    try:
        import rdkit  # type: ignore[import]
        pytest.skip("RDKit installed — placeholder path not tested")
    except ImportError:
        mol = MoleculeLayout.from_smiles("CCO")
        assert isinstance(mol, VGroup)
        assert len(mol.atoms) == 1  # placeholder "?"


def test_molecule_triangle():
    """Cyclopropane-like 3-atom triangle."""
    import math
    r = 1.0
    atoms = [
        {"symbol": "C", "position": (r * math.cos(2*math.pi*i/3), r * math.sin(2*math.pi*i/3))}
        for i in range(3)
    ]
    bonds = [{"a": 0, "b": 1}, {"a": 1, "b": 2}, {"a": 2, "b": 0}]
    mol = MoleculeLayout.from_atoms_bonds(atoms, bonds)
    assert len(mol.atoms) == 3
    assert len(mol.bonds) == 3


# ── ReactionArrow ─────────────────────────────────────────────────────────────

def test_reaction_arrow_no_conditions():
    ra = ReactionArrow((-2.0, 0.0), (2.0, 0.0))
    assert isinstance(ra, VGroup)
    assert len(ra.submobjects) == 1  # arrow only


def test_reaction_arrow_above():
    ra = ReactionArrow((-2.0, 0.0), (2.0, 0.0), conditions_above=r"\Delta")
    assert len(ra.submobjects) == 2  # arrow + above label


def test_reaction_arrow_both():
    ra = ReactionArrow((-2.0, 0.0), (2.0, 0.0),
                       conditions_above=r"\Delta",
                       conditions_below=r"\mathrm{H_2O}")
    assert len(ra.submobjects) == 3  # arrow + above + below


def test_reaction_arrow_renders():
    class RAScene(Scene):
        def construct(self):
            ra = ReactionArrow((-2.5, 0.0), (2.5, 0.0),
                               conditions_above=r"\Delta")
            self.add(ra)
            self.play(FadeIn(ra, run_time=0.3))
            self.wait(0.2)
    scene = RAScene()
    _attach(scene)
    scene.construct()
