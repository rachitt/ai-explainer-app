"""chalk.chemistry — domain primitive kit for chemistry/reaction scenes.

Pure compositions of C1 primitives. No new renderer features.

RDKit is an optional dependency; from_smiles() degrades gracefully without it.

Exports: Atom, Bond, MoleculeLayout, ReactionArrow
"""
from __future__ import annotations

import math

import numpy as np

from chalk.vgroup import VGroup
from chalk.style import PRIMARY, YELLOW, BLUE, GREEN, GREY, RED_FILL, SCALE_LABEL, SCALE_ANNOT
from chalk.connectable import Connectable, circle_edge_toward, get_center, resolve_endpoint


class Atom(VGroup):
    """Labeled atom circle with optional charge annotation.

    symbol: element symbol, e.g. "C", "O", "N"
    charge: "" | "+" | "-" | "2+" | "2-" etc.
    color: stroke and label color; fill is slightly transparent.
    """

    def __init__(
        self,
        symbol: str,
        position: tuple[float, float] = (0.0, 0.0),
        charge: str = "",
        color: str = PRIMARY,
        radius: float = 0.32,
    ) -> None:
        from chalk.shapes import Circle
        from chalk.tex import MathTex

        self.position = np.array(position, dtype=float)
        lbl = MathTex(
            rf"\mathrm{{{symbol}}}",
            color=color, scale=SCALE_LABEL,
        )
        xmin, ymin, xmax, ymax = lbl.bbox()
        label_hw = (xmax - xmin) / 2
        label_hh = (ymax - ymin) / 2
        self.fitted_radius = max(radius, max(label_hw, label_hh) + 0.12)

        circle = Circle(
            radius=self.fitted_radius, color=color,
            fill_color=color, fill_opacity=0.15,
            stroke_width=2.5,
        )
        circle.shift(position[0], position[1])
        lbl.move_to(position[0], position[1])

        mobs: list = [circle, lbl]
        if charge:
            charge_lbl = MathTex(
                rf"{{\scriptstyle {charge}}}",
                color=color, scale=SCALE_ANNOT,
            )
            charge_lbl.move_to(
                position[0] + self.fitted_radius + 0.12,
                position[1] + self.fitted_radius - 0.05,
            )
            mobs.append(charge_lbl)

        super().__init__(*mobs)

    @property
    def center(self) -> tuple[float, float]:
        return (float(self.position[0]), float(self.position[1]))

    def edge_toward(self, target: tuple[float, float]) -> tuple[float, float]:
        return circle_edge_toward(
            float(self.position[0]),
            float(self.position[1]),
            self.fitted_radius,
            target,
        )


class Bond(VGroup):
    """Bond between two Atom positions.

    order: 1 (single), 2 (double), 3 (triple).
    stereo: "plain" | "wedge" | "dash".
    """

    def __init__(
        self,
        a: Connectable | tuple[float, float],
        b: Connectable | tuple[float, float],
        order: int = 1,
        stereo: str = "plain",
        color: str = PRIMARY,
        stroke_width: float = 2.0,
    ) -> None:
        from chalk.shapes import Line, Polygon

        a_is_connectable = isinstance(a, Connectable)
        b_is_connectable = isinstance(b, Connectable)

        pa = np.array(get_center(a), dtype=float)
        pb = np.array(get_center(b), dtype=float)
        chord = pb - pa
        length = float(np.linalg.norm(chord))
        if length < 1e-9:
            super().__init__()
            return

        u = chord / length
        perp = np.array([-u[1], u[0]])

        if a_is_connectable or b_is_connectable:
            start = np.array(resolve_endpoint(a, get_center(b)), dtype=float)
            end = np.array(resolve_endpoint(b, get_center(a)), dtype=float)
        else:
            # Back-compat for raw tuple endpoints: preserve the old fixed atom shrink.
            atom_r = 0.32
            shrink = min(atom_r, length / 3)
            start = pa + shrink * u
            end = pb - shrink * u

        mobs: list = []

        if stereo == "wedge":
            # Filled triangle: narrow at start, wide at end
            w = stroke_width * 0.08
            verts = [
                tuple(start),
                tuple(end + w * perp),
                tuple(end - w * perp),
            ]
            mobs.append(Polygon(*verts, color=color, fill_color=color, fill_opacity=1.0,
                                stroke_width=0.0))
        elif stereo == "dash":
            # Dashed bond: N short perpendicular lines
            n_dashes = 6
            for i in range(n_dashes):
                t = i / (n_dashes - 1)
                center = start + t * (end - start)
                half_w = (stroke_width * 0.04) * (1 + t)  # widens toward end
                d_start = center + half_w * perp
                d_end = center - half_w * perp
                mobs.append(Line(
                    (float(d_start[0]), float(d_start[1])),
                    (float(d_end[0]), float(d_end[1])),
                    color=color, stroke_width=stroke_width * 0.8,
                ))
        else:
            # Plain single bond
            mobs.append(Line(
                (float(start[0]), float(start[1])),
                (float(end[0]), float(end[1])),
                color=color, stroke_width=stroke_width,
            ))

        if order >= 2:
            sep = stroke_width * 0.06
            for sign in (-1.0, 1.0):
                offset = sign * sep * perp
                mobs.append(Line(
                    (float(start[0] + offset[0]), float(start[1] + offset[1])),
                    (float(end[0] + offset[0]), float(end[1] + offset[1])),
                    color=color, stroke_width=stroke_width * 0.7,
                ))
            # Remove first single line if order > 1 (already have two parallel lines)
            # For double bond: replace the single center line with two offset ones
            if stereo == "plain":
                mobs = mobs[1:]  # drop the first (center) line, keep the two offset ones

        if order == 3:
            mobs.append(Line(
                (float(start[0]), float(start[1])),
                (float(end[0]), float(end[1])),
                color=color, stroke_width=stroke_width,
            ))

        super().__init__(*mobs)


class MoleculeLayout(VGroup):
    """A molecule assembled from Atom + Bond objects.

    Use from_atoms_bonds() to build directly from dicts,
    or from_smiles() for SMILES parsing (requires RDKit).
    """

    def __init__(self, atoms: list[Atom], bonds: list[Bond]) -> None:
        self.atoms = atoms
        self.bonds = bonds
        super().__init__(*bonds, *atoms)  # bonds behind atoms

    @classmethod
    def from_atoms_bonds(
        cls,
        atoms: list[dict],
        bonds: list[dict],
        color_map: "dict[str, str] | None" = None,
    ) -> "MoleculeLayout":
        """Build from atom/bond dicts.

        atoms: [{"symbol": "C", "position": (x, y)}, ...]
        bonds: [{"a": 0, "b": 1, "order": 1, "stereo": "plain"}, ...]
        color_map: {"C": PRIMARY, "O": RED_FILL, ...}
        """
        default_colors: dict[str, str] = {
            "C": PRIMARY, "H": GREY, "O": RED_FILL,
            "N": BLUE, "S": YELLOW, "F": GREEN,
        }
        cmap = {**default_colors, **(color_map or {})}

        atom_mobs = [
            Atom(
                symbol=a["symbol"],
                position=tuple(a["position"]),
                charge=a.get("charge", ""),
                color=cmap.get(a["symbol"], PRIMARY),
                radius=a.get("radius", 0.32),
            )
            for a in atoms
        ]

        from chalk.layout import check_no_overlap
        check_no_overlap(atom_mobs, min_sep=0.50)

        bond_mobs = [
            Bond(
                a=atom_mobs[b["a"]],
                b=atom_mobs[b["b"]],
                order=b.get("order", 1),
                stereo=b.get("stereo", "plain"),
            )
            for b in bonds
        ]

        return cls(atom_mobs, bond_mobs)

    @classmethod
    def from_smiles(
        cls,
        smiles: str,
        scale: float = 1.5,
        color_map: "dict[str, str] | None" = None,
    ) -> "MoleculeLayout":
        """Parse SMILES and layout molecule using RDKit's 2D coordinates.

        Falls back to a single-atom placeholder if RDKit is not installed.
        """
        try:
            from rdkit import Chem  # type: ignore[import]
            from rdkit.Chem import AllChem, rdMolDescriptors  # type: ignore[import]
            from rdkit.Chem import Draw  # type: ignore[import]
        except ImportError:
            # Graceful degradation: return a single atom labeled with the SMILES
            placeholder = Atom("?", position=(0.0, 0.0), color=GREY)
            return cls([placeholder], [])

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            placeholder = Atom("?", position=(0.0, 0.0), color=GREY)
            return cls([placeholder], [])

        AllChem.Compute2DCoords(mol)
        conf = mol.GetConformer()

        positions_raw = [
            np.array([conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y])
            for i in range(mol.GetNumAtoms())
        ]
        # Scale and center
        center = np.mean(positions_raw, axis=0)
        positions = [(pos - center) * scale for pos in positions_raw]

        atoms_dicts = [
            {
                "symbol": mol.GetAtomWithIdx(i).GetSymbol(),
                "position": (float(positions[i][0]), float(positions[i][1])),
                "charge": _charge_str(mol.GetAtomWithIdx(i).GetFormalCharge()),
            }
            for i in range(mol.GetNumAtoms())
        ]

        bond_order_map = {
            1: 1, 2: 2, 3: 3,
            12: 1,  # aromatic → single for display
        }
        bonds_dicts = [
            {
                "a": bond.GetBeginAtomIdx(),
                "b": bond.GetEndAtomIdx(),
                "order": bond_order_map.get(int(bond.GetBondTypeAsDouble()), 1),
            }
            for bond in mol.GetBonds()
        ]

        return cls.from_atoms_bonds(atoms_dicts, bonds_dicts, color_map)


def _charge_str(charge: int) -> str:
    if charge == 0:
        return ""
    if charge == 1:
        return "+"
    if charge == -1:
        return "-"
    return f"{charge:+d}"


def ReactionArrow(
    start: tuple[float, float],
    end: tuple[float, float],
    conditions_above: str = "",
    conditions_below: str = "",
    color: str = PRIMARY,
) -> VGroup:
    """Reaction arrow with optional condition labels above and below.

    Returns a VGroup of arrow + condition labels.
    """
    from chalk.shapes import Arrow
    from chalk.tex import MathTex

    arrow = Arrow(start, end, color=color, head_length=0.22, head_width=0.18, shaft_width=0.05)
    mobs: list = [arrow]

    pa = np.array(start, dtype=float)
    pb = np.array(end, dtype=float)
    mid = (pa + pb) / 2
    chord = pb - pa
    perp = np.array([-chord[1], chord[0]])
    if np.linalg.norm(perp) > 1e-9:
        perp = perp / np.linalg.norm(perp)

    if conditions_above:
        lbl = MathTex(conditions_above, color=GREY, scale=SCALE_ANNOT)
        pos = mid + 0.4 * perp
        lbl.move_to(float(pos[0]), float(pos[1]))
        mobs.append(lbl)

    if conditions_below:
        lbl = MathTex(conditions_below, color=GREY, scale=SCALE_ANNOT)
        pos = mid - 0.4 * perp
        lbl.move_to(float(pos[0]), float(pos[1]))
        mobs.append(lbl)

    return VGroup(*mobs)
