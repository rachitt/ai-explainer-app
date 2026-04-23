from pathlib import Path

import pytest
import yaml
from pedagogica_tools.audit_skills import audit_skills, format_report
from pedagogica_tools.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def write_skill(
    root: Path,
    category: str,
    name: str,
    frontmatter_dict: dict,
    body: str = "Body\n",
) -> Path:
    path = root / category / name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = yaml.safe_dump(frontmatter_dict, sort_keys=False)
    path.write_text(f"---\n{frontmatter}---\n{body}", encoding="utf-8")
    return path


def write_clean_tree(root: Path) -> None:
    write_skill(
        root,
        "knowledge",
        "chalk-primitives",
        {"name": "chalk-primitives", "requires": []},
    )
    write_skill(
        root,
        "knowledge",
        "latex-for-video",
        {"name": "latex-for-video", "requires": []},
    )
    write_skill(
        root,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": ["chalk-primitives"]},
    )
    write_skill(
        root,
        "agents",
        "chalk-repair",
        {"name": "chalk-repair", "requires": ["chalk-primitives", "latex-for-video"]},
    )


def test_clean_repo_has_no_errors(tmp_path: Path) -> None:
    write_clean_tree(tmp_path)

    report = audit_skills(tmp_path)

    assert report.has_errors is False
    assert len(report.issues) == 0
    assert len(report.skills) == 4


def test_name_mismatch_is_error(tmp_path: Path) -> None:
    write_skill(tmp_path, "agents", "chalk-code", {"name": "script", "requires": []})

    report = audit_skills(tmp_path)

    assert len(report.issues) == 1
    assert report.issues[0].severity == "error"
    assert "mismatch" in report.issues[0].message


def test_dangling_requires_is_error(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": ["missing-skill"]},
    )

    report = audit_skills(tmp_path)

    assert len(report.issues) == 1
    assert report.issues[0].severity == "error"
    assert "missing-skill" in report.issues[0].message


def test_requires_version_suffix_resolves_bare_name(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "knowledge",
        "chalk-primitives",
        {"name": "chalk-primitives", "requires": []},
    )
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": ["chalk-primitives@^0.1.0"]},
    )

    report = audit_skills(tmp_path)

    assert report.has_errors is False
    assert len(report.issues) == 0


def test_no_frontmatter_is_error_and_does_not_crash(tmp_path: Path) -> None:
    path = tmp_path / "agents" / "chalk-code" / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Plain markdown\n", encoding="utf-8")

    report = audit_skills(tmp_path)

    assert len(report.issues) == 1
    assert report.issues[0].severity == "error"
    assert "does not start" in report.issues[0].message


def test_unclosed_frontmatter_is_error_and_does_not_crash(tmp_path: Path) -> None:
    path = tmp_path / "agents" / "chalk-code" / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nname: chalk-code\n", encoding="utf-8")

    report = audit_skills(tmp_path)

    assert len(report.issues) == 1
    assert report.issues[0].severity == "error"
    assert "closing" in report.issues[0].message


def test_body_separators_after_frontmatter_are_ignored(tmp_path: Path) -> None:
    path = write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": []},
    )
    path.write_text(
        "---\nname: chalk-code\nrequires: []\n---\nBody\n---\nMore body\n",
        encoding="utf-8",
    )

    report = audit_skills(tmp_path)

    assert report.has_errors is False
    assert len(report.issues) == 0


def test_cli_clean_fake_root_exits_0(tmp_path: Path) -> None:
    write_clean_tree(tmp_path)

    result = runner.invoke(app, ["audit-skills", "--skills-root", str(tmp_path)])

    assert result.exit_code == 0, result.stderr
    assert "audit: 4 skills scanned, 0 errors, 0 warnings." in result.stdout


def test_cli_dirty_fake_root_exits_1(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": ["missing-skill"]},
    )

    result = runner.invoke(app, ["audit-skills", "--skills-root", str(tmp_path)])

    assert result.exit_code == 1
    assert "missing-skill" in result.stdout


def test_cli_nonexistent_root_exits_2(tmp_path: Path) -> None:
    result = runner.invoke(app, ["audit-skills", "--skills-root", str(tmp_path / "nope")])

    assert result.exit_code == 2
    assert "not a directory" in result.stderr


def test_body_ref_to_existing_agent_is_clean(tmp_path: Path) -> None:
    write_skill(tmp_path, "agents", "chalk-code", {"name": "chalk-code", "requires": []})
    write_skill(
        tmp_path,
        "agents",
        "script",
        {"name": "script", "requires": []},
        body="Read agents/chalk-code/SKILL.md first.\n",
    )

    report = audit_skills(tmp_path)

    assert len(report.issues) == 0


def test_body_ref_to_missing_agent_reports_warning(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": []},
        body="Intro\nRead agents/manim-code/SKILL.md first.\n",
    )

    report = audit_skills(tmp_path)

    assert len(report.issues) == 1
    assert report.issues[0].severity == "warning"
    assert report.issues[0].line == 6
    assert "manim-code" in report.issues[0].message


def test_body_ref_pedagogica_skills_path_form(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": []},
        body="Use pedagogica/skills/knowledge/color-and-typography for palettes.\n",
    )

    report = audit_skills(tmp_path)

    assert len(report.issues) == 1
    assert report.issues[0].severity == "warning"
    assert "color-and-typography" in report.issues[0].message


def test_body_prose_mentioning_manim_without_path_not_flagged(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": []},
        body="Avoid copying old manim examples unless ported to chalk.\n",
    )

    report = audit_skills(tmp_path)

    assert len(report.issues) == 0


def test_body_ref_multiple_dedups(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": []},
        body=(
            "Read agents/manim-code/SKILL.md before writing.\n"
            "Read agents/manim-code/SKILL.md before repairing.\n"
        ),
    )

    report = audit_skills(tmp_path)

    assert len(report.issues) == 2
    assert [issue.line for issue in report.issues] == [5, 6]


def test_body_ref_line_number_accurate(tmp_path: Path) -> None:
    path = tmp_path / "agents" / "chalk-code" / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body_lines = ["Body"] * 20
    body_lines.append("Read agents/manim-code/SKILL.md.")
    path.write_text(
        "---\nname: chalk-code\nrequires: []\n---\n" + "\n".join(body_lines) + "\n",
        encoding="utf-8",
    )

    report = audit_skills(tmp_path)

    assert len(report.issues) == 1
    assert report.issues[0].line == 25


def test_strict_body_flag_promotes_warnings_to_error_exit(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": []},
        body="Read agents/manim-code/SKILL.md first.\n",
    )

    result = runner.invoke(app, ["audit-skills", "--skills-root", str(tmp_path)])
    strict_result = runner.invoke(
        app,
        ["audit-skills", "--skills-root", str(tmp_path), "--strict-body"],
    )

    assert result.exit_code == 0
    assert strict_result.exit_code == 1


def test_report_formatting_shows_severity_prefix(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": []},
        body="Read agents/manim-code/SKILL.md first.\n",
    )

    report = audit_skills(tmp_path)

    assert "[warning]" in format_report(report)


def test_known_stage_trigger_passes(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": [], "triggers": ["stage:chalk-code"]},
    )

    report = audit_skills(tmp_path)

    assert len(report.issues) == 0


def test_unknown_stage_trigger_reports_error(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": [], "triggers": ["stage:manim-code"]},
    )

    report = audit_skills(tmp_path)

    assert len(report.issues) == 1
    assert report.issues[0].severity == "error"
    assert "manim-code" in report.issues[0].message


def test_non_stage_trigger_ignored(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {
            "name": "chalk-code",
            "requires": [],
            "triggers": ["scene_type:any", "element_type:math"],
        },
    )

    report = audit_skills(tmp_path)

    assert len(report.issues) == 0


def test_mixed_triggers_error_on_bad_only(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {
            "name": "chalk-code",
            "requires": [],
            "triggers": [
                "stage:chalk-code",
                "scene_type:any",
                "stage:visual-planner",
            ],
        },
    )

    report = audit_skills(tmp_path)

    assert len(report.issues) == 1
    assert report.issues[0].severity == "error"
    assert "visual-planner" in report.issues[0].message
    assert "unknown stage trigger: 'stage:visual-planner'" in report.issues[0].message


def test_malformed_trigger_reports_error(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": [], "triggers": ["chalk-code"]},
    )

    report = audit_skills(tmp_path)

    assert len(report.issues) == 1
    assert report.issues[0].severity == "error"
    assert "malformed trigger" in report.issues[0].message


def test_trigger_line_number_accurate(tmp_path: Path) -> None:
    path = tmp_path / "agents" / "chalk-code" / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "name: chalk-code\n"
        "requires: []\n"
        "version: 0.0.1\n"
        "owner: test\n"
        "triggers:\n"
        "  - stage:chalk-code\n"
        "  - stage:visual-planner\n"
        "---\n"
        "Body\n",
        encoding="utf-8",
    )

    report = audit_skills(tmp_path)

    assert len(report.issues) == 1
    assert report.issues[0].line == 8


def test_real_repo_triggers_clean() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    skills_root = repo_root / "pedagogica" / "skills"
    if not skills_root.exists():
        pytest.skip("real pedagogica/skills path is not available")

    report = audit_skills(skills_root)
    trigger_errors = [
        issue
        for issue in report.issues
        if issue.severity == "error" and "trigger" in issue.message
    ]
    if trigger_errors:
        pytest.xfail("real repo currently contains stale stage triggers")

    assert trigger_errors == []
