from pathlib import Path

import yaml
from pedagogica_tools.audit_skills import audit_skills
from pedagogica_tools.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def write_skill(root: Path, category: str, name: str, frontmatter_dict: dict) -> Path:
    path = root / category / name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = yaml.safe_dump(frontmatter_dict, sort_keys=False)
    path.write_text(f"---\n{frontmatter}---\nBody\n", encoding="utf-8")
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
    assert "audit: 4 skills scanned, 0 issues." in result.stdout


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
