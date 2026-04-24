from __future__ import annotations

from uuid import uuid4

import pytest
from pedagogica_schemas.intake import IntakeResult
from pedagogica_schemas.storyboard import SceneBeat, Storyboard
from pydantic import ValidationError


def _base_intake(*, hook_question: str) -> IntakeResult:
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


def _base_storyboard(*, hook_question: str) -> Storyboard:
    return Storyboard(
        trace_id=uuid4(),
        span_id=uuid4(),
        producer="test",
        topic="chain rule",
        hook_question=hook_question,
        total_duration_seconds=15.0,
        scenes=[
            SceneBeat(
                scene_id="scene_01",
                beat_type="hook",
                target_duration_seconds=15.0,
                learning_objective_id=None,
                visual_intent="show a puzzling derivative setup",
                narration_intent="ask why the extra factor appears",
                required_skills=[],
            )
        ],
        palette={"bg": "#0b0f1a"},
        voice_id="voice",
    )


def test_intake_result_accepts_valid_hook_question() -> None:
    result = _base_intake(
        hook_question="why does the derivative of sin(x^2) have that extra 2x out front?"
    )

    assert result.hook_question.endswith("?")


def test_intake_result_rejects_hook_question_without_question_mark() -> None:
    with pytest.raises(ValidationError):
        _base_intake(
            hook_question="why does the derivative of sin(x^2) have that extra 2x out front"
        )


def test_intake_result_rejects_hook_question_shorter_than_six_chars() -> None:
    with pytest.raises(ValidationError):
        _base_intake(hook_question="why?")


def test_storyboard_accepts_valid_hook_question() -> None:
    result = _base_storyboard(
        hook_question="why does the derivative of sin(x^2) have that extra 2x out front?"
    )

    assert result.hook_question.endswith("?")


def test_storyboard_rejects_hook_question_without_question_mark() -> None:
    with pytest.raises(ValidationError):
        _base_storyboard(
            hook_question="why does the derivative of sin(x^2) have that extra 2x out front"
        )


def test_storyboard_rejects_hook_question_shorter_than_six_chars() -> None:
    with pytest.raises(ValidationError):
        _base_storyboard(hook_question="why?")
