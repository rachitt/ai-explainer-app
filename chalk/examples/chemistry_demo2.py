"""Second chalk.chemistry demo -- acid-base neutralization.

Run: uv run chalk chalk/examples/chemistry_demo2.py --scene AcidBaseDemo -o out.mp4
"""
import math

from chalk.chemistry import Molecule

from chalk import (
    GREEN,
    GREY,
    PRIMARY,
    SCALE_BODY,
    SCALE_LABEL,
    YELLOW,
    ZONE_BOTTOM,
    ZONE_TOP,
    Arrow,
    FadeIn,
    MathTex,
    Scene,
    VGroup,
    next_to,
    place_in_zone,
)


class AcidBaseDemo(Scene):
    def construct(self):
        def hcl(origin_x: float) -> VGroup:
            return Molecule(
                [
                    {"symbol": "H", "position": (origin_x - 0.6, 0.8)},
                    {"symbol": "Cl", "position": (origin_x + 0.7, 0.8)},
                ],
                [{"a": 0, "b": 1}],
                caption=r"\mathrm{HCl}",
                color_map={"Cl": GREEN},
            )

        def naoh(origin_x: float) -> VGroup:
            return Molecule(
                [
                    {"symbol": "Na", "position": (origin_x - 1.0, -0.8)},
                    {"symbol": "O", "position": (origin_x + 0.1, -0.8)},
                    {"symbol": "H", "position": (origin_x + 1.2, -0.8)},
                ],
                [{"a": 1, "b": 2}],
                caption=r"\mathrm{NaOH}",
                color_map={"Na": GREEN},
            )

        def reactants() -> VGroup:
            plus = MathTex(r"+", color=PRIMARY, scale=SCALE_BODY)
            plus.move_to(-3.0, 0.0)
            return VGroup(hcl(-4.7), plus, naoh(-1.4))

        def nacl(origin_x: float) -> VGroup:
            return Molecule(
                [
                    {"symbol": "Na", "position": (origin_x - 0.6, 0.6), "charge": "+"},
                    {"symbol": "Cl", "position": (origin_x + 0.6, 0.6), "charge": "-"},
                ],
                [],
                caption=r"\mathrm{NaCl}",
                color_map={"Na": GREEN, "Cl": GREEN},
            )

        def water(origin_x: float) -> VGroup:
            bond_len = 1.1
            half_angle = math.radians(104.5 / 2)
            o_pos = (origin_x, -0.8)
            h_y = -0.8 - bond_len * math.cos(half_angle)
            h1_pos = (origin_x - bond_len * math.sin(half_angle), h_y)
            h2_pos = (origin_x + bond_len * math.sin(half_angle), h_y)
            return Molecule(
                [
                    {"symbol": "O", "position": o_pos},
                    {"symbol": "H", "position": h1_pos},
                    {"symbol": "H", "position": h2_pos},
                ],
                [{"a": 0, "b": 1}, {"a": 0, "b": 2}],
                caption=r"\mathrm{H_2O}",
            )

        def products() -> VGroup:
            plus = MathTex(r"+", color=PRIMARY, scale=SCALE_BODY)
            plus.move_to(3.0, 0.0)
            return VGroup(nacl(1.6), plus, water(4.7))

        # -- Beat 1: reactants -----------------------------------------------
        lhs = reactants()
        caption = MathTex(r"\mathrm{acid + base}", color=GREY, scale=SCALE_BODY)
        place_in_zone(caption, ZONE_BOTTOM)
        self.add(lhs, caption)
        self.play(FadeIn(lhs, run_time=0.8), FadeIn(caption, run_time=0.5))
        self.wait(1.0)
        self.clear()

        # -- Beat 2: neutralization arrow ------------------------------------
        lhs = reactants()
        rhs = products()
        rhs.shift(0.2, 0.0)
        arrow = Arrow((-0.3, 0.0), (1.4, 0.0), color=YELLOW)
        neutralize = MathTex(r"\mathrm{neutralize}", color=YELLOW, scale=SCALE_LABEL)
        next_to(neutralize, arrow, direction="UP", buff=0.25)
        self.add(lhs, rhs, arrow, neutralize)
        self.play(FadeIn(lhs, run_time=0.5), FadeIn(rhs, run_time=0.5))
        self.play(FadeIn(arrow, run_time=0.5), FadeIn(neutralize, run_time=0.5))
        self.wait(1.2)
        self.clear()

        # -- Beat 3: salt and water products ---------------------------------
        rhs = products()
        product_caption = MathTex(r"\mathrm{salt + water}", color=GREY, scale=SCALE_BODY)
        place_in_zone(product_caption, ZONE_TOP)
        self.add(rhs, product_caption)
        self.play(FadeIn(rhs, run_time=0.8), FadeIn(product_caption, run_time=0.5))
        self.wait(2.0)
