"""Claude Code — 45 s beginner explainer.

Five discrete scenes, each cleared via `self.clear()` before the next.

    Scene 1   0 –  5 s   Title card
    Scene 2   5 – 13 s   User prompt meets the agent
    Scene 3  13 – 25 s   Agent reaches for its tools
    Scene 4  25 – 37 s   Tools edit files and tests pass
    Scene 5  37 – 45 s   Takeaway
"""
from chalk import (
    Scene, Circle, Rectangle, Arrow, MathTex,
    FadeIn,
    PRIMARY, YELLOW, BLUE, GREEN, GREY, TRACK,
    SCALE_DISPLAY, SCALE_BODY, SCALE_LABEL, SCALE_ANNOT,
)


def _agent_with_label(x: float, y: float, radius: float = 0.85) -> tuple:
    """A labeled agent hub: yellow circle + small 'agent' caption below."""
    circle = Circle(radius=radius, color=YELLOW, fill_color=YELLOW,
                    fill_opacity=0.18, stroke_width=3.0)
    circle.shift(x, y)
    label = MathTex(r"\mathrm{agent}", color=YELLOW, scale=SCALE_ANNOT)
    label.move_to(x, y - radius - 0.35)
    return circle, label


class ClaudeCode(Scene):
    def construct(self) -> None:
        # ── Scene 1 — Title card ─────────────────────────────────
        title   = MathTex(r"\mathrm{Claude\ Code}",
                          color=YELLOW, scale=SCALE_DISPLAY)
        title.move_to(0, 0.5)
        tagline = MathTex(r"\mathrm{an\ AI\ coding\ agent\ in\ your\ terminal}",
                          color=GREY, scale=SCALE_LABEL)
        tagline.move_to(0, -0.5)

        self.add(title, tagline)
        self.play(FadeIn(title,   run_time=0.8))
        self.play(FadeIn(tagline, run_time=0.6))
        self.wait(2.0)
        self.clear()

        # ── Scene 2 — Prompt → agent ─────────────────────────────
        prompt_box  = Rectangle(width=5.0, height=1.0,
                                color=BLUE, stroke_width=2.5)
        prompt_box.shift(-3.6, 0.0)
        prompt_text = MathTex(r"\mathrm{fix\ the\ login\ bug}",
                              color=BLUE, scale=SCALE_LABEL)
        prompt_text.move_to(-3.6, 0.0)

        agent2, agent2_lbl = _agent_with_label(x=3.0, y=0.0)

        arrow_in = Arrow((-0.95, 0.0), (2.00, 0.0),
                         color=PRIMARY, stroke_width=2.0,
                         head_length=0.3, head_width=0.25, shaft_width=0.06)

        self.add(prompt_box, prompt_text)
        self.play(FadeIn(prompt_box,  run_time=0.6),
                  FadeIn(prompt_text, run_time=0.6),
                  run_time=0.7)
        self.wait(1.0)

        self.add(arrow_in)
        self.play(FadeIn(arrow_in, run_time=0.5))

        self.add(agent2, agent2_lbl)
        self.play(FadeIn(agent2,     run_time=0.6),
                  FadeIn(agent2_lbl, run_time=0.6),
                  run_time=0.7)
        self.wait(3.0)
        self.clear()

        # ── Scene 3 — Tools fan out ──────────────────────────────
        agent3, agent3_lbl = _agent_with_label(x=-3.5, y=0.0)

        def make_tool(label: str, x: float, y: float) -> tuple:
            box = Rectangle(width=1.9, height=0.85,
                            color=PRIMARY, stroke_width=2.5)
            box.shift(x, y)
            lbl = MathTex(fr"\mathrm{{{label}}}",
                          color=PRIMARY, scale=SCALE_LABEL)
            lbl.move_to(x, y)
            return box, lbl

        read_box, read_lbl = make_tool("Read",  3.3,  1.8)
        edit_box, edit_lbl = make_tool("Edit",  3.3,  0.0)
        bash_box, bash_lbl = make_tool("Bash",  3.3, -1.8)

        def make_link(y: float) -> Arrow:
            # Agent center at (-3.5, 0), radius 0.85; exit at x=-2.6.
            # Tool boxes centered at (3.3, y) with width 1.9; left edge at x=2.35.
            return Arrow((-2.55, y * 0.35), (2.25, y),
                         color=TRACK, stroke_width=1.5,
                         head_length=0.22, head_width=0.2, shaft_width=0.04)

        link_r, link_e, link_b = make_link(1.8), make_link(0.0), make_link(-1.8)

        self.add(agent3, agent3_lbl)
        self.play(FadeIn(agent3,     run_time=0.5),
                  FadeIn(agent3_lbl, run_time=0.5),
                  run_time=0.6)
        self.wait(0.6)

        self.add(link_r, read_box, read_lbl)
        self.play(FadeIn(link_r,   run_time=0.4),
                  FadeIn(read_box, run_time=0.6),
                  FadeIn(read_lbl, run_time=0.6),
                  run_time=0.6)
        self.wait(0.6)

        self.add(link_e, edit_box, edit_lbl)
        self.play(FadeIn(link_e,   run_time=0.4),
                  FadeIn(edit_box, run_time=0.6),
                  FadeIn(edit_lbl, run_time=0.6),
                  run_time=0.6)
        self.wait(0.6)

        self.add(link_b, bash_box, bash_lbl)
        self.play(FadeIn(link_b,   run_time=0.4),
                  FadeIn(bash_box, run_time=0.6),
                  FadeIn(bash_lbl, run_time=0.6),
                  run_time=0.6)
        self.wait(6.2)
        self.clear()

        # ── Scene 4 — Files get fixed, tests pass ────────────────
        row_y = 0.4

        def make_file(label: str, x: float, color: str = GREY) -> tuple:
            box = Rectangle(width=2.4, height=0.9,
                            color=color, stroke_width=2.2)
            box.shift(x, row_y)
            lbl = MathTex(fr"\mathrm{{{label}}}",
                          color=color, scale=SCALE_LABEL)
            lbl.move_to(x, row_y)
            return box, lbl

        auth_box,   auth_lbl   = make_file("auth.py", -3.5)
        test_box,   test_lbl   = make_file("tests",    0.0)
        readme_box, readme_lbl = make_file("README",   3.5)

        self.add(auth_box, auth_lbl, test_box, test_lbl, readme_box, readme_lbl)
        self.play(FadeIn(auth_box,   run_time=0.5), FadeIn(auth_lbl,   run_time=0.5),
                  FadeIn(test_box,   run_time=0.5), FadeIn(test_lbl,   run_time=0.5),
                  FadeIn(readme_box, run_time=0.5), FadeIn(readme_lbl, run_time=0.5),
                  run_time=0.6)
        self.wait(1.2)

        # auth.py goes green
        auth_box_fixed = Rectangle(width=2.4, height=0.9,
                                   color=GREEN, fill_color=GREEN,
                                   fill_opacity=0.15, stroke_width=2.5)
        auth_box_fixed.shift(-3.5, row_y)
        auth_lbl_fixed = MathTex(r"\mathrm{auth.py}",
                                 color=GREEN, scale=SCALE_LABEL)
        auth_lbl_fixed.move_to(-3.5, row_y)

        self.remove(auth_box, auth_lbl)
        self.add(auth_box_fixed, auth_lbl_fixed)
        self.play(FadeIn(auth_box_fixed, run_time=0.6),
                  FadeIn(auth_lbl_fixed, run_time=0.6),
                  run_time=0.6)
        self.wait(1.2)

        # tests go green with a "pass" caption beneath
        test_box_pass = Rectangle(width=2.4, height=0.9,
                                  color=GREEN, fill_color=GREEN,
                                  fill_opacity=0.15, stroke_width=2.5)
        test_box_pass.shift(0.0, row_y)
        test_lbl_pass = MathTex(r"\mathrm{tests}",
                                color=GREEN, scale=SCALE_LABEL)
        test_lbl_pass.move_to(0.0, row_y)
        pass_lbl = MathTex(r"\mathrm{pass}", color=GREEN, scale=SCALE_ANNOT)
        pass_lbl.move_to(0.0, row_y - 0.95)

        self.remove(test_box, test_lbl)
        self.add(test_box_pass, test_lbl_pass, pass_lbl)
        self.play(FadeIn(test_box_pass, run_time=0.6),
                  FadeIn(test_lbl_pass, run_time=0.6),
                  FadeIn(pass_lbl,      run_time=0.6),
                  run_time=0.6)
        self.wait(6.2)
        self.clear()

        # ── Scene 5 — Takeaway ───────────────────────────────────
        t1 = MathTex(r"\mathrm{give\ it\ a\ goal}",
                     color=YELLOW, scale=SCALE_BODY)
        t1.move_to(0, 0.7)
        t2 = MathTex(r"\mathrm{it\ plans,\ edits,\ and\ verifies}",
                     color=PRIMARY, scale=SCALE_BODY)
        t2.move_to(0, -0.5)

        self.add(t1)
        self.play(FadeIn(t1, run_time=0.8))
        self.wait(0.8)
        self.add(t2)
        self.play(FadeIn(t2, run_time=0.8))
        self.wait(9.0)
