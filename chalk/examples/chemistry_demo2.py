"""Second chalk.chemistry demo -- acid-base neutralization.

Run: uv run chalk chalk/examples/chemistry_demo2.py --scene AcidBaseDemo -o out.mp4
"""
import math

from chalk import (
    Scene,
    VGroup,
    FadeIn,
    MathTex,
    Arrow,
    PRIMARY,
    YELLOW,
    GREEN,
    GREY,
    RED_FILL,
    SCALE_LABEL,
    SCALE_BODY,
    ZONE_TOP,
    ZONE_BOTTOM,
    place_in_zone,
    next_to,
)
from chalk.chemistry import Atom, Bond


class AcidBaseDemo(Scene):
    def construct(self):
        def bbox_of(mob):
            if isinstance(mob, VGroup):
                boxes = [bbox_of(child) for child in mob.submobjects]
                return (
                    min(box[0] for box in boxes),
                    min(box[1] for box in boxes),
                    max(box[2] for box in boxes),
                    max(box[3] for box in boxes),
                )
            pts = mob.points
            return (
                float(pts[:, 0].min()),
                float(pts[:, 1].min()),
                float(pts[:, 0].max()),
                float(pts[:, 1].max()),
            )

        def place_formula(label: MathTex, molecule_body: VGroup) -> None:
            xmin, ymin, xmax, _ = bbox_of(molecule_body)
            label.move_to((xmin + xmax) / 2, ymin - 0.55)

        def hcl(origin_x: float) -> VGroup:
            h = Atom("H", position=(origin_x - 0.6, 0.8), color=GREY)
            cl = Atom("Cl", position=(origin_x + 0.7, 0.8), color=GREEN)
            bond = Bond(h, cl, color=PRIMARY)
            label = MathTex(r"\mathrm{HCl}", color=GREY, scale=SCALE_LABEL)
            place_formula(label, VGroup(bond, h, cl))
            return VGroup(bond, h, cl, label)

        def naoh(origin_x: float) -> VGroup:
            na = Atom("Na", position=(origin_x - 1.0, -0.8), color=GREEN)
            o = Atom("O", position=(origin_x + 0.1, -0.8), color=RED_FILL)
            h = Atom("H", position=(origin_x + 1.2, -0.8), color=GREY)
            bond_oh = Bond(o, h, color=PRIMARY)
            label = MathTex(r"\mathrm{NaOH}", color=GREY, scale=SCALE_LABEL)
            place_formula(label, VGroup(na, bond_oh, o, h))
            return VGroup(na, bond_oh, o, h, label)

        def reactants() -> VGroup:
            plus = MathTex(r"+", color=PRIMARY, scale=SCALE_BODY)
            plus.move_to(-3.0, 0.0)
            return VGroup(hcl(-4.7), plus, naoh(-1.4))

        def nacl(origin_x: float) -> VGroup:
            na = Atom("Na", position=(origin_x - 0.6, 0.6), charge="+", color=GREEN)
            cl = Atom("Cl", position=(origin_x + 0.6, 0.6), charge="-", color=GREEN)
            label = MathTex(r"\mathrm{NaCl}", color=GREY, scale=SCALE_LABEL)
            place_formula(label, VGroup(na, cl))
            return VGroup(na, cl, label)

        def water(origin_x: float) -> VGroup:
            bond_len = 1.1
            half_angle = math.radians(104.5 / 2)
            o_pos = (origin_x, -0.8)
            h1_pos = (origin_x - bond_len * math.sin(half_angle), -0.8 - bond_len * math.cos(half_angle))
            h2_pos = (origin_x + bond_len * math.sin(half_angle), -0.8 - bond_len * math.cos(half_angle))
            o = Atom("O", position=o_pos, color=RED_FILL)
            h1 = Atom("H", position=h1_pos, color=GREY)
            h2 = Atom("H", position=h2_pos, color=GREY)
            b1 = Bond(o, h1, color=PRIMARY)
            b2 = Bond(o, h2, color=PRIMARY)
            label = MathTex(r"\mathrm{H_2O}", color=GREY, scale=SCALE_LABEL)
            place_formula(label, VGroup(b1, b2, o, h1, h2))
            return VGroup(b1, b2, o, h1, h2, label)

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
