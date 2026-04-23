from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import yaml


@dataclass(frozen=True)
class SkillIssue:
    skill_path: Path
    severity: str
    message: str


@dataclass(frozen=True)
class SkillInfo:
    path: Path
    category: str
    dir_name: str
    frontmatter_name: str | None
    requires: list[str]


@dataclass(frozen=True)
class AuditReport:
    skills: list[SkillInfo]
    issues: list[SkillIssue]

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)


def iter_skill_files(skills_root: Path) -> Iterator[Path]:
    """Yield agents/*/SKILL.md and knowledge/*/SKILL.md in deterministic order."""
    paths: list[Path] = []
    for category in ("agents", "knowledge"):
        paths.extend((skills_root / category).glob("*/SKILL.md"))
    yield from sorted(paths, key=lambda path: (path.parent.parent.name, path.parent.name))


def parse_frontmatter(path: Path) -> tuple[dict | None, str | None]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, "file does not start with frontmatter delimiter '---'"

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "file does not start with frontmatter delimiter '---'"

    closing_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        return None, "no closing frontmatter delimiter '---' found"

    frontmatter_text = "\n".join(lines[1:closing_index])
    try:
        parsed = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as e:
        return None, f"YAML parse error: {e}"

    if not isinstance(parsed, dict):
        return None, "frontmatter must parse to a YAML mapping"

    return parsed, None


def parse_skill(path: Path) -> tuple[SkillInfo | None, list[SkillIssue]]:
    frontmatter, error = parse_frontmatter(path)
    if error is not None:
        return None, [SkillIssue(path, "error", error)]

    assert frontmatter is not None
    raw_requires = frontmatter.get("requires") or []
    if isinstance(raw_requires, str):
        requires_entries = [raw_requires]
    else:
        requires_entries = list(raw_requires)

    requires = [
        str(entry).split("@", 1)[0].strip()
        for entry in requires_entries
        if str(entry).split("@", 1)[0].strip()
    ]

    frontmatter_name = frontmatter.get("name")
    if frontmatter_name is not None:
        frontmatter_name = str(frontmatter_name).strip()

    return (
        SkillInfo(
            path=path,
            category=path.parent.parent.name,
            dir_name=path.parent.name,
            frontmatter_name=frontmatter_name,
            requires=requires,
        ),
        [],
    )


def audit_skills(skills_root: Path) -> AuditReport:
    skills: list[SkillInfo] = []
    issues: list[SkillIssue] = []

    for path in iter_skill_files(skills_root):
        skill, skill_issues = parse_skill(path)
        issues.extend(skill_issues)
        if skill is not None:
            skills.append(skill)

    known_names = {skill.frontmatter_name for skill in skills if skill.frontmatter_name}

    for skill in skills:
        if not skill.frontmatter_name:
            issues.append(SkillIssue(skill.path, "error", "name field is missing"))
            continue

        if skill.frontmatter_name != skill.dir_name:
            issues.append(
                SkillIssue(
                    skill.path,
                    "error",
                    f"name mismatch: frontmatter name {skill.frontmatter_name!r} "
                    f"does not match directory {skill.dir_name!r}",
                )
            )

        for required_name in skill.requires:
            if required_name not in known_names:
                issues.append(
                    SkillIssue(
                        skill.path,
                        "error",
                        f"dangling requires entry: {required_name!r} does not resolve "
                        "to a scanned SKILL name",
                    )
                )

    return AuditReport(skills=skills, issues=issues)


def format_report(report: AuditReport) -> str:
    lines: list[str] = []
    issues_by_path: dict[Path, list[SkillIssue]] = defaultdict(list)
    for issue in report.issues:
        issues_by_path[issue.skill_path].append(issue)

    for path in sorted(issues_by_path):
        lines.append(str(path))
        for issue in issues_by_path[path]:
            lines.append(f"  {issue.severity}: {issue.message}")

    lines.append(f"audit: {len(report.skills)} skills scanned, {len(report.issues)} issues.")
    return "\n".join(lines)
