from __future__ import annotations

import json
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterator

from pedagogica_schemas.registry import SCHEMA_REGISTRY
from pydantic import ValidationError


@dataclass(frozen=True)
class ArtifactIssue:
    path: Path
    schema: str
    message: str


FILE_TO_SCHEMA: list[tuple[str, str]] = [
    ("scenes/*/audio/clip.json", "AudioClip"),
    ("scenes/*/script.json", "Script"),
    ("scenes/*/code.json", "ChalkCode"),
    ("scenes/*/compile_attempt_*.json", "CompileResult"),
    ("scenes/*/sync.json", "SyncPlan"),
    ("01_intake.json", "IntakeResult"),
    ("02_curriculum.json", "CurriculumPlan"),
    ("03_storyboard.json", "Storyboard"),
    ("job_state.json", "JobState"),
]


def classify_artifact(path: Path, job_dir: Path) -> str | None:
    relative_path = path.relative_to(job_dir).as_posix()
    for pattern, schema_name in FILE_TO_SCHEMA:
        if fnmatch(relative_path, pattern):
            return schema_name
    return None


def iter_candidate_json(job_dir: Path) -> Iterator[Path]:
    patterns = ("*.json", "scenes/*/*.json", "scenes/*/audio/*.json")
    seen: set[Path] = set()
    for pattern in patterns:
        for path in sorted(job_dir.glob(pattern)):
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            yield path


def count_unknown_artifacts(job_dir: Path) -> int:
    return sum(
        1
        for path in iter_candidate_json(job_dir)
        if classify_artifact(path, job_dir) is None
    )


def audit_artifacts(job_dir: Path) -> tuple[list[ArtifactIssue], int]:
    issues: list[ArtifactIssue] = []
    scanned_count = 0

    for path in iter_candidate_json(job_dir):
        schema_name = classify_artifact(path, job_dir)
        if schema_name is None:
            continue

        scanned_count += 1
        model_cls = SCHEMA_REGISTRY[schema_name]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            model_cls.model_validate(data)
        except json.JSONDecodeError as e:
            issues.append(ArtifactIssue(path, schema_name, f"invalid JSON: {e}"))
        except ValidationError as e:
            issues.append(ArtifactIssue(path, schema_name, e.json(indent=2)))

    return issues, scanned_count
