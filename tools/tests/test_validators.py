from __future__ import annotations

from uuid import uuid4

import pytest
from pedagogica_schemas.intake import IntakeResult
from pedagogica_schemas.storyboard import SceneBeat, Storyboard
from pedagogica_schemas.validators import validate_hook_question_propagation
from pydantic import ValidationError


def _intake(*, hook_question: str) -> IntakeResult:
    return IntakeResult(
        trace_id=uuid4(),
        span_id=uuid4(),
        producer="test",
        topic="chain rule",
        hook_question=hook_question,
        domain="calculus",
        audience_level="undergrad",
        target_length_seconds=180,
    )


def _storyboard(*, hook_question: str, narration_intent: str) -> Storyboard:
    return Storyboard(
        trace_id=uuid4(),
        span_id=uuid4(),
        producer="test",
        topic="chain rule",
        hook_question=hook_question,
        total_duration_seconds=30.0,
        scenes=[
            SceneBeat(
                scene_id="scene_01",
                beat_type="hook",
                target_duration_seconds=30.0,
                learning_objective_id=None,
                visual_intent="show the changing slope on sin of x squared",
                narration_intent=narration_intent,
                required_skills=[],
            )
        ],
        palette={"bg": "#0b0f1a"},
        voice_id="voice",
    )


def test_hook_question_mismatch_reports_error() -> None:
    report = validate_hook_question_propagation(
        _intake(hook_question="why does the derivative of sin(x^2) have that extra 2x out front?"),
        _storyboard(
            hook_question="why does the derivative of cos(x^2) have that extra 2x out front?",
            narration_intent="we set up why that extra 2x appears",
        ),
    )

    assert not report.passed
    assert any(issue.rule == "hook_question_mismatch" for issue in report.issues)
    assert any(issue.severity == "error" for issue in report.issues)


def test_hook_question_match_with_salient_token_passes_cleanly() -> None:
    report = validate_hook_question_propagation(
        _intake(hook_question="why does the derivative of sin(x^2) have that extra 2x out front?"),
        _storyboard(
            hook_question="why does the derivative of sin(x^2) have that extra 2x out front?",
            narration_intent="we focus on where that extra factor comes from",
        ),
    )

    assert report.passed
    assert report.issues == []


def test_hook_question_match_without_salient_token_warns_only() -> None:
    report = validate_hook_question_propagation(
        _intake(hook_question="why does the derivative of sin(x^2) have that extra 2x out front?"),
        _storyboard(
            hook_question="why does the derivative of sin(x^2) have that extra 2x out front?",
            narration_intent="we start with a mystery and then unpack the answer step by step",
        ),
    )

    assert report.passed
    assert [issue.rule for issue in report.issues] == ["hook_beat_not_anchored"]
    assert report.issues[0].severity == "warn"


def test_hook_question_without_question_mark_fails_schema_validation() -> None:
    with pytest.raises(ValidationError):
        _intake(hook_question="why does the derivative of sin(x^2) have that extra 2x out front")
