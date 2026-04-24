import json
from pathlib import Path

import yaml
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


def write_clean_skills(root: Path) -> None:
    write_skill(
        root,
        "knowledge",
        "chalk-primitives",
        {"name": "chalk-primitives", "requires": []},
    )
    write_skill(
        root,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": ["chalk-primitives"]},
    )


def write_valid_intake(job_dir: Path) -> None:
    payload = {
        "trace_id": "00000000-0000-0000-0000-000000000001",
        "span_id": "00000000-0000-0000-0000-000000000002",
        "parent_span_id": None,
        "timestamp": "2026-04-22T12:00:00+00:00",
        "producer": "intake",
        "schema_version": "0.1.0",
        "topic": "derivatives",
        "hook_question": "why does the slope change as the curve bends?",
        "domain": "calculus",
        "audience_level": "undergrad",
        "target_length_seconds": 120,
        "style_hints": [],
        "clarification_needed": False,
        "clarification_question": None,
    }
    (job_dir / "01_intake.json").write_text(json.dumps(payload), encoding="utf-8")


def test_audit_skill_only_clean_exits_0(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    write_clean_skills(skills_root)

    result = runner.invoke(app, ["audit", "--skills-root", str(skills_root)])

    assert result.exit_code == 0, result.stdout
    assert "SKILL audit" in result.stdout
    assert "skipped (no job_dir)" in result.stdout
    assert "overall: clean" in result.stdout


def test_audit_skill_only_dirty_dangling_requires_exits_1(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    write_skill(
        skills_root,
        "agents",
        "chalk-code",
        {"name": "chalk-code", "requires": ["missing-skill"]},
    )

    result = runner.invoke(app, ["audit", "--skills-root", str(skills_root)])

    assert result.exit_code == 1
    assert "missing-skill" in result.stdout
    assert "overall: 1 issues" in result.stdout


def test_audit_full_clean_valid_intake_exits_0(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    job_dir = tmp_path / "job"
    job_dir.mkdir()
    write_clean_skills(skills_root)
    write_valid_intake(job_dir)

    result = runner.invoke(app, ["audit", str(job_dir), "--skills-root", str(skills_root)])

    assert result.exit_code == 0, result.stdout
    assert "artifact audit" in result.stdout
    assert "1 artifacts scanned, 0 issues" in result.stdout
    assert "overall: clean" in result.stdout


def test_audit_full_broken_artifact_exits_1(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    job_dir = tmp_path / "job"
    job_dir.mkdir()
    write_clean_skills(skills_root)
    (job_dir / "01_intake.json").write_text("{}", encoding="utf-8")

    result = runner.invoke(app, ["audit", str(job_dir), "--skills-root", str(skills_root)])

    assert result.exit_code == 1
    assert "01_intake.json" in result.stdout
    assert "IntakeResult" in result.stdout
    assert "overall: 1 issues" in result.stdout


def test_audit_skips_unknown_random_json_exits_0(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    job_dir = tmp_path / "job"
    job_dir.mkdir()
    write_clean_skills(skills_root)
    (job_dir / "random.json").write_text("{}", encoding="utf-8")

    result = runner.invoke(app, ["audit", str(job_dir), "--skills-root", str(skills_root)])

    assert result.exit_code == 0, result.stdout
    assert "0 artifacts scanned, 0 issues, skipped count=1" in result.stdout
    assert "overall: clean" in result.stdout


def test_audit_nonexistent_job_dir_exits_2(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    write_clean_skills(skills_root)

    result = runner.invoke(
        app,
        ["audit", str(tmp_path / "missing-job"), "--skills-root", str(skills_root)],
    )

    assert result.exit_code == 2
    assert "not a directory" in result.stderr


def test_audit_invalid_skills_root_exits_2(tmp_path: Path) -> None:
    result = runner.invoke(app, ["audit", "--skills-root", str(tmp_path / "missing")])

    assert result.exit_code == 2
    assert "not a directory" in result.stderr
