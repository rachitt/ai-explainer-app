from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from pedagogica_schemas.script import Script
from pedagogica_schemas.storyboard import Storyboard

_WORD_RE = re.compile(r"\b\w[\w']*\b")
_FIRST_PERSON_RE = re.compile(r"\b(we|we'?ve|we'?re|let'?s|our|us)\b", re.IGNORECASE)
_DEMO_ACTION_RE = re.compile(
    r"\b(watch|notice|here|ready|boom|look|see|try|imagine)\b", re.IGNORECASE
)


@dataclass
class ScriptCadenceIssue:
    rule: str
    severity: Literal["error", "warn"]
    observed: float | int | str
    threshold: float | int | str
    message: str


@dataclass
class ScriptCadenceReport:
    scene_id: str
    issues: list[ScriptCadenceIssue] = field(default_factory=list)
    passed: bool = True
    quotas_met: int = 0


@dataclass
class DepthBudgetIssue:
    rule: str
    severity: Literal["error", "warn"]
    observed: int | float
    threshold: int | float
    message: str


@dataclass
class DepthBudgetReport:
    topic: str
    total_duration_seconds: float
    lo_count_in_depth: int
    issues: list[DepthBudgetIssue] = field(default_factory=list)
    passed: bool = True


def _tokenize_words(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _tokenize_sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"[.?!](?:\s|$)", text) if sentence.strip()]


def validate_script_cadence(
    script: Script, target_duration_seconds: float, beat_type: str
) -> ScriptCadenceReport:
    words = _tokenize_words(script.text)
    word_count = len(words)
    report = ScriptCadenceReport(scene_id=script.scene_id)

    # Rule 1: word budget
    words_per_second = round(word_count / target_duration_seconds, 2)
    if word_count / target_duration_seconds > 2.75:
        report.issues.append(
            ScriptCadenceIssue(
                rule="word_budget",
                severity="error",
                observed=words_per_second,
                threshold=2.75,
                message=f"Word rate {words_per_second:.2f} wps exceeds 2.75 ceiling — script will rush.",
            )
        )
        report.passed = False
    else:
        report.quotas_met += 1

    # Rule 2: short sentence ratio
    if word_count < 25:
        report.quotas_met += 1
    else:
        sentences = _tokenize_sentences(script.text)
        short_sentence_count = sum(
            1 for sentence in sentences if len(_tokenize_words(sentence)) <= 6
        )
        short_sentence_ratio = (
            short_sentence_count / len(sentences) if sentences else 0.0
        )
        short_sentence_ratio = round(short_sentence_ratio, 2)
        if short_sentence_ratio < 0.25:
            report.issues.append(
                ScriptCadenceIssue(
                    rule="short_sentence_ratio",
                    severity="warn",
                    observed=short_sentence_ratio,
                    threshold=0.25,
                    message=(
                        f"Short-sentence ratio {short_sentence_ratio:.2f} is below the 0.25 floor."
                    ),
                )
            )
        else:
            report.quotas_met += 1

    # Rule 3: question density
    if beat_type == "recap":
        report.quotas_met += 1
    else:
        question_count = script.text.count("?")
        question_target = word_count / 40
        question_density = round(question_count / question_target, 2) if question_target else 0.0
        if question_count < question_target:
            report.issues.append(
                ScriptCadenceIssue(
                    rule="question_density",
                    severity="warn",
                    observed=question_density,
                    threshold=1.0,
                    message=(
                        f"Question density {question_density:.2f} is below the 1.00 target."
                    ),
                )
            )
        else:
            report.quotas_met += 1

    # Rule 4: first-person density
    first_person_count = len(_FIRST_PERSON_RE.findall(script.text))
    first_person_threshold = round(8 * word_count / 100, 2)
    if first_person_count < first_person_threshold:
        report.issues.append(
            ScriptCadenceIssue(
                rule="first_person_density",
                severity="warn",
                observed=first_person_count,
                threshold=first_person_threshold,
                message=(
                    "First-person markers are below the 8-per-100-words floor."
                ),
            )
        )
    else:
        report.quotas_met += 1

    # Rule 5: demo-action words
    if beat_type == "recap":
        report.quotas_met += 1
    else:
        demo_action_count = len(_DEMO_ACTION_RE.findall(script.text))
        if demo_action_count < 2:
            report.issues.append(
                ScriptCadenceIssue(
                    rule="demo_action_words",
                    severity="warn",
                    observed=demo_action_count,
                    threshold=2,
                    message="Demo-action vocabulary is below the 2-word floor.",
                )
            )
        else:
            report.quotas_met += 1

    return report


def validate_script(script: Script, storyboard: Storyboard) -> ScriptCadenceReport:
    beat = next((scene for scene in storyboard.scenes if scene.scene_id == script.scene_id), None)
    if beat is None:
        raise ValueError(
            f"scene_id {script.scene_id!r} not found in storyboard scenes"
        )
    return validate_script_cadence(
        script,
        beat.target_duration_seconds,
        beat.beat_type,
    )


