"""Claude Code — 45 s beginner explainer.

What it is: an AI coding agent that takes a plain-English goal and carries it
out in your repository by calling a small set of tools (read, edit, run).

Duration breakdown:
    0 –  4 s   Title + tagline
    4 – 12 s   User prompt box + flow arrow
   12 – 24 s   Agent hub + tool boxes fan out
   24 – 34 s   Loop: read → edit → test, then result
   34 – 45 s   Takeaway caption
"""
from chalk import (
    Scene, Circle, Rectangle, Line, Arrow, MathTex,
    FadeIn, FadeOut,
    PRIMARY, YELLOW, BLUE, GREEN, GREY, TRACK,
    SCALE_DISPLAY, SCALE_BODY, SCALE_LABEL, SCALE_ANNOT,
    next_to,
)


class ClaudeCode(Scene):
    def construct(self) -> None:
        # ── 0 – 4 s   Title ───────────────────────────────────────
        title = MathTex(r"\mathrm{Claude\ Code}",
                        color=YELLOW, scale=SCALE_DISPLAY)
        title.move_to(0, 3.1)
        self.add(title)
        self.play(FadeIn(title, run_time=0.8))

        tagline = MathTex(r"\mathrm{an\ AI\ coding\ agent\ in\ your\ terminal}",
                          color=GREY, scale=SCALE_ANNOT)
        tagline.move_to(0, 2.35)
        self.add(tagline)
        self.play(FadeIn(tagline, run_time=0.6))
        self.wait(2.0)

        # ── 4 – 12 s   Prompt → agent ────────────────────────────
        # User prompt box on the left
        prompt_box = Rectangle(width=3.9, height=0.9,
                               color=BLUE, stroke_width=2.5)
        prompt_box.shift(-4.0, 0.5)
        prompt_text = MathTex(r"\mathrm{fix\ the\ login\ bug}",
                              color=BLUE, scale=SCALE_LABEL)
        prompt_text.move_to(-4.0, 0.5)

        self.add(prompt_box, prompt_text)
        self.play(FadeIn(prompt_box, run_time=0.6),
                  FadeIn(prompt_text, run_time=0.6),
                  run_time=0.7)
        self.wait(1.5)

        # Arrow from prompt box to agent
        arrow1 = Arrow((-1.95, 0.5), (-0.8, 0.5),
                       color=PRIMARY, stroke_width=2.0,
                       head_length=0.25, head_width=0.22, shaft_width=0.06)
        self.add(arrow1)
        self.play(FadeIn(arrow1, run_time=0.4))
        self.wait(0.4)

        # Agent hub: circle with label inside
        agent = Circle(radius=0.7, color=YELLOW, fill_color=YELLOW,
                       fill_opacity=0.18, stroke_width=3.0)
        agent.shift(0, 0.5)
        agent_lbl = MathTex(r"\mathrm{agent}",
                            color=YELLOW, scale=SCALE_LABEL)
        agent_lbl.move_to(0, 0.5)

        self.add(agent, agent_lbl)
        self.play(FadeIn(agent, run_time=0.6),
                  FadeIn(agent_lbl, run_time=0.6),
                  run_time=0.7)
        self.wait(2.0)

        # ── 12 – 24 s   Tools fan out ────────────────────────────
        # Three tool boxes on the right: Read, Edit, Bash
        def tool(label: str, x: float, y: float, color: str) -> tuple:
            box = Rectangle(width=1.7, height=0.75,
                            color=color, stroke_width=2.5)
            box.shift(x, y)
            lbl = MathTex(fr"\mathrm{{{label}}}",
                          color=color, scale=SCALE_LABEL)
            lbl.move_to(x, y)
            return box, lbl

        read_box, read_lbl = tool("Read",  2.7,  1.8, PRIMARY)
        edit_box, edit_lbl = tool("Edit",  2.7,  0.5, PRIMARY)
        bash_box, bash_lbl = tool("Bash",  2.7, -0.8, PRIMARY)

        # Arrows from agent to tools
        arr_r = Arrow((0.7, 0.9),  (1.85,  1.8),
                      color=TRACK, stroke_width=1.5,
                      head_length=0.2, head_width=0.18, shaft_width=0.04)
        arr_e = Arrow((0.7, 0.5),  (1.85,  0.5),
                      color=TRACK, stroke_width=1.5,
                      head_length=0.2, head_width=0.18, shaft_width=0.04)
        arr_b = Arrow((0.7, 0.1),  (1.85, -0.8),
                      color=TRACK, stroke_width=1.5,
                      head_length=0.2, head_width=0.18, shaft_width=0.04)

        self.add(arr_r, arr_e, arr_b,
                 read_box, read_lbl,
                 edit_box, edit_lbl,
                 bash_box, bash_lbl)
        self.play(
            FadeIn(arr_r,    run_time=0.5),
            FadeIn(read_box, run_time=0.7),
            FadeIn(read_lbl, run_time=0.7),
            run_time=0.7,
        )
        self.wait(0.7)
        self.play(
            FadeIn(arr_e,    run_time=0.5),
            FadeIn(edit_box, run_time=0.7),
            FadeIn(edit_lbl, run_time=0.7),
            run_time=0.7,
        )
        self.wait(0.7)
        self.play(
            FadeIn(arr_b,    run_time=0.5),
            FadeIn(bash_box, run_time=0.7),
            FadeIn(bash_lbl, run_time=0.7),
            run_time=0.7,
        )
        self.wait(3.0)

        # ── 24 – 34 s   Loop + result ────────────────────────────
        # Files row at the bottom; one of them goes GREEN when fixed.
        files_y = -2.1
        auth_box = Rectangle(width=1.4, height=0.6, color=GREY, stroke_width=2.0)
        auth_box.shift(-3.0, files_y)
        auth_lbl = MathTex(r"\mathrm{auth.py}", color=GREY, scale=SCALE_ANNOT)
        auth_lbl.move_to(-3.0, files_y)

        test_box = Rectangle(width=1.4, height=0.6, color=GREY, stroke_width=2.0)
        test_box.shift(-1.2, files_y)
        test_lbl = MathTex(r"\mathrm{tests}", color=GREY, scale=SCALE_ANNOT)
        test_lbl.move_to(-1.2, files_y)

        repo_box = Rectangle(width=1.4, height=0.6, color=GREY, stroke_width=2.0)
        repo_box.shift(0.6, files_y)
        repo_lbl = MathTex(r"\mathrm{README}", color=GREY, scale=SCALE_ANNOT)
        repo_lbl.move_to(0.6, files_y)

        self.add(auth_box, auth_lbl, test_box, test_lbl, repo_box, repo_lbl)
        self.play(
            FadeIn(auth_box, run_time=0.5), FadeIn(auth_lbl, run_time=0.5),
            FadeIn(test_box, run_time=0.5), FadeIn(test_lbl, run_time=0.5),
            FadeIn(repo_box, run_time=0.5), FadeIn(repo_lbl, run_time=0.5),
            run_time=0.6,
        )
        self.wait(1.5)

        # Swap auth.py to GREEN (edit succeeded)
        auth_box_fixed = Rectangle(width=1.4, height=0.6,
                                   color=GREEN, fill_color=GREEN,
                                   fill_opacity=0.15, stroke_width=2.5)
        auth_box_fixed.shift(-3.0, files_y)
        auth_lbl_fixed = MathTex(r"\mathrm{auth.py}",
                                 color=GREEN, scale=SCALE_ANNOT)
        auth_lbl_fixed.move_to(-3.0, files_y)

        self.add(auth_box_fixed, auth_lbl_fixed)
        self.play(
            FadeOut(auth_box, run_time=0.4),
            FadeOut(auth_lbl, run_time=0.4),
            FadeIn(auth_box_fixed, run_time=0.6),
            FadeIn(auth_lbl_fixed, run_time=0.6),
            run_time=0.6,
        )

        # "tests pass" — green check-ish label next to tests
        tests_ok = MathTex(r"\mathrm{pass}", color=GREEN, scale=SCALE_ANNOT)
        tests_ok.move_to(-1.2, files_y - 0.6)
        self.add(tests_ok)
        self.play(FadeIn(tests_ok, run_time=0.5))
        self.wait(6.5)

        # ── 34 – 45 s   Takeaway ─────────────────────────────────
        caption = MathTex(
            r"\mathrm{give\ it\ a\ goal\ \rightarrow\ it\ plans,\ edits,\ and\ verifies}",
            color=PRIMARY, scale=SCALE_LABEL,
        )
        caption.move_to(0, -3.15)
        self.add(caption)
        self.play(FadeIn(caption, run_time=0.8))
        self.wait(19.0)
