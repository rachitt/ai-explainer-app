import re
from dataclasses import dataclass, field
from typing import Literal

from pedagogica_schemas.intake import IntakeResult
from pedagogica_schemas.storyboard import Storyboard

STOPWORDS = {
    "the",
    "a",
    "an",
    "why",
    "how",
    "what",
    "when",
    "where",
    "does",
    "do",
    "is",
    "are",
    "it",
    "of",
    "to",
    "from",
    "in",
    "on",
    "that",
    "this",
    "at",
    "for",
    "with",
}


@dataclass
class HookQuestionIssue:
    rule: str
    severity: Literal["error", "warn"]
    message: str


@dataclass
class HookQuestionReport:
    intake_hook_question: str
    storyboard_hook_question: str
    issues: list[HookQuestionIssue] = field(default_factory=list)
    passed: bool = True


def _salient_tokens(text: str) -> set[str]:
    normalized = re.sub(r"[^\w\s]", " ", text.lower())
    return {
        token
        for token in normalized.split()
        if len(token) >= 4 and token not in STOPWORDS
    }


def validate_hook_question_propagation(
    intake: IntakeResult, storyboard: Storyboard
) -> HookQuestionReport:
    report = HookQuestionReport(
        intake_hook_question=intake.hook_question,
        storyboard_hook_question=storyboard.hook_question,
    )

    if storyboard.hook_question.strip() != intake.hook_question.strip():
        report.issues.append(
            HookQuestionIssue(
                rule="hook_question_mismatch",
                severity="error",
                message="storyboard.hook_question must match intake.hook_question exactly",
            )
        )

    first_scene = storyboard.scenes[0] if storyboard.scenes else None
    if first_scene is not None and first_scene.beat_type == "hook":
        narration = first_scene.narration_intent.lower()
        salient_tokens = _salient_tokens(intake.hook_question)
        if salient_tokens and not any(token in narration for token in salient_tokens):
            report.issues.append(
                HookQuestionIssue(
                    rule="hook_beat_not_anchored",
                    severity="warn",
                    message=(
                        "hook beat narration_intent should reuse at least one salient token "
                        "from the hook_question"
                    ),
                )
            )

    report.passed = not any(issue.severity == "error" for issue in report.issues)
    return report
