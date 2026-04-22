"""chalk.chemistry demo — Atom, Bond, MoleculeLayout, ReactionArrow.

Beats:
1. Individual atoms with charges
2. Water molecule (H₂O) with bonds
3. CO₂ with double bonds
4. SN2-style reaction: A → B with reagent arrow

Run: uv run chalk chalk/examples/chemistry_demo.py --scene ChemistryDemo -o out.mp4
"""
import math
from chalk import (
    Scene, VGroup,
    FadeIn, FadeOut, Write,
    PRIMARY, YELLOW, BLUE, GREEN, GREY, RED_FILL,
    SCALE_DISPLAY, SCALE_LABEL,
    MathTex, next_to,
)
from chalk.chemistry import Atom, Bond, MoleculeLayout, ReactionArrow


class ChemistryDemo(Scene):
    def construct(self):

        # ── Beat 1: atom gallery ─────────────────────────────────────────────
        specs = [
            ("C",  (-4.5, 0.0), "",  PRIMARY),
            ("O",  (-1.5, 0.0), "",  RED_FILL),
            ("N",  ( 1.5, 0.0), "",  BLUE),
            ("Na", ( 4.5, 0.0), "+", GREEN),
        ]
        atoms = []
        for sym, pos, chg, col in specs:
            a = Atom(sym, position=pos, charge=chg, color=col)
            atoms.append(a)
            self.add(a)
        self.play(*[FadeIn(a, run_time=0.4) for a in atoms])
        self.wait(1.5)
        self.clear()

        # ── Beat 2: water molecule ───────────────────────────────────────────
        angle = math.radians(104.5 / 2)  # H–O–H bond angle half
        bond_len = 1.4
        o_pos  = (0.0, 0.0)
        h1_pos = (-bond_len * math.sin(angle), -bond_len * math.cos(angle))
        h2_pos = ( bond_len * math.sin(angle), -bond_len * math.cos(angle))

        water = MoleculeLayout.from_atoms_bonds(
            atoms=[
                {"symbol": "O", "position": o_pos},
                {"symbol": "H", "position": h1_pos},
                {"symbol": "H", "position": h2_pos},
            ],
            bonds=[
                {"a": 0, "b": 1, "order": 1},
                {"a": 0, "b": 2, "order": 1},
            ],
        )
        lbl_water = MathTex(r"\mathrm{H_2O\ —\ Water}", color=GREY, scale=0.75)
        lbl_water.move_to(0.0, 3.0)
        self.add(lbl_water, water)
        self.play(FadeIn(lbl_water, run_time=0.4), FadeIn(water, run_time=0.7))
        self.wait(1.5)
        self.clear()

        # ── Beat 3: CO₂ with double bonds ───────────────────────────────────
        co2 = MoleculeLayout.from_atoms_bonds(
            atoms=[
                {"symbol": "O", "position": (-2.2, 0.0)},
                {"symbol": "C", "position": ( 0.0, 0.0)},
                {"symbol": "O", "position": ( 2.2, 0.0)},
            ],
            bonds=[
                {"a": 0, "b": 1, "order": 2},
                {"a": 1, "b": 2, "order": 2},
            ],
        )
        lbl_co2 = MathTex(r"\mathrm{CO_2\ —\ Carbon\ dioxide}", color=GREY, scale=0.75)
        lbl_co2.move_to(0.0, 3.0)
        self.add(lbl_co2, co2)
        self.play(FadeIn(lbl_co2, run_time=0.4), FadeIn(co2, run_time=0.7))
        self.wait(1.5)
        self.clear()

        # ── Beat 4: reaction A → B with wedge/dash stereo bonds ─────────────
        # Reactant: tetrahedral carbon with 4 bonds
        r_pos = (-3.5, 0.0)
        reactant = MoleculeLayout.from_atoms_bonds(
            atoms=[
                {"symbol": "C",  "position": r_pos},
                {"symbol": "Cl", "position": (r_pos[0] - 1.2, r_pos[1])},
                {"symbol": "H",  "position": (r_pos[0],       r_pos[1] + 1.2)},
                {"symbol": "H",  "position": (r_pos[0],       r_pos[1] - 1.2)},
                {"symbol": "Br", "position": (r_pos[0] + 1.2, r_pos[1])},
            ],
            bonds=[
                {"a": 0, "b": 1, "order": 1},
                {"a": 0, "b": 2, "order": 1, "stereo": "wedge"},
                {"a": 0, "b": 3, "order": 1, "stereo": "dash"},
                {"a": 0, "b": 4, "order": 1},
            ],
        )

        # Product: similar but Br replaced by Nu
        p_pos = (3.5, 0.0)
        product = MoleculeLayout.from_atoms_bonds(
            atoms=[
                {"symbol": "C",  "position": p_pos},
                {"symbol": "Nu", "position": (p_pos[0] - 1.2, p_pos[1])},
                {"symbol": "H",  "position": (p_pos[0],       p_pos[1] + 1.2)},
                {"symbol": "H",  "position": (p_pos[0],       p_pos[1] - 1.2)},
                {"symbol": "Cl", "position": (p_pos[0] + 1.2, p_pos[1])},
            ],
            bonds=[
                {"a": 0, "b": 1, "order": 1},
                {"a": 0, "b": 2, "order": 1, "stereo": "dash"},
                {"a": 0, "b": 3, "order": 1, "stereo": "wedge"},
                {"a": 0, "b": 4, "order": 1},
            ],
        )

        rxn_arrow = ReactionArrow(
            (-1.2, 0.0), (1.2, 0.0),
            conditions_above=r"Nu^-",
            conditions_below=r"S_N2",
            color=YELLOW,
        )
        lbl_rxn = MathTex(r"\mathrm{Inversion\ of\ configuration}", color=GREY, scale=0.65)
        lbl_rxn.move_to(0.0, 3.0)

        self.add(lbl_rxn, reactant)
        self.play(FadeIn(lbl_rxn, run_time=0.4), FadeIn(reactant, run_time=0.6))
        self.add(rxn_arrow)
        self.play(FadeIn(rxn_arrow, run_time=0.5))
        self.add(product)
        self.play(FadeIn(product, run_time=0.6))
        self.wait(2.0)
        self.clear()
