from uuid import uuid4

import pytest
from pedagogica_schemas import (
    SCHEMA_REGISTRY,
    CurriculumPlan,
    IntakeResult,
    JobState,
    LearningObjective,
    SceneBeat,
    StageStatus,
    Storyboard,
)
from pydantic import ValidationError


def _meta(producer: str) -> dict:
    return {
        "trace_id": str(uuid4()),
        "span_id": str(uuid4()),
        "producer": producer,
        "schema_version": "0.0.1",
    }


def test_registry_has_planning_schemas() -> None:
    assert {"IntakeResult", "CurriculumPlan", "Storyboard", "JobState"} <= set(SCHEMA_REGISTRY)


def test_intake_result_round_trip() -> None:
    payload = {
        **_meta("intake"),
        "topic": "chain rule",
        "domain": "calculus",
        "audience_level": "undergrad",
        "target_length_seconds": 180,
        "style_hints": ["3blue1brown"],
        "clarification_needed": False,
        "clarification_question": None,
    }
    parsed = IntakeResult.model_validate(payload)
    assert parsed.topic == "chain rule"
    IntakeResult.model_validate_json(parsed.model_dump_json())


def test_intake_rejects_out_of_range_length() -> None:
    with pytest.raises(ValidationError):
        IntakeResult.model_validate(
            {
                **_meta("intake"),
                "topic": "chain rule",
                "domain": "calculus",
                "audience_level": "undergrad",
                "target_length_seconds": 10,
            }
        )


def test_intake_clarification_consistency() -> None:
    with pytest.raises(ValidationError):
        IntakeResult.model_validate(
            {
                **_meta("intake"),
                "topic": "chain rule",
                "domain": "calculus",
                "audience_level": "undergrad",
                "target_length_seconds": 180,
                "clarification_needed": True,
                "clarification_question": None,
            }
        )


def test_curriculum_sequence_must_match_objectives() -> None:
    base = {
        **_meta("curriculum"),
        "topic": "chain rule",
        "objectives": [
            LearningObjective(id="LO1", text="understand composition of functions").model_dump(),
            LearningObjective(
                id="LO2", text="apply chain rule", prerequisites=["LO1"]
            ).model_dump(),
        ],
    }
    CurriculumPlan.model_validate({**base, "sequence": ["LO1", "LO2"]})

    with pytest.raises(ValidationError):
        CurriculumPlan.model_validate({**base, "sequence": ["LO2", "LO1"]})

    with pytest.raises(ValidationError):
        CurriculumPlan.model_validate({**base, "sequence": ["LO1", "LO3"]})


def test_curriculum_rejects_unknown_prerequisite() -> None:
    with pytest.raises(ValidationError):
        CurriculumPlan.model_validate(
            {
                **_meta("curriculum"),
                "topic": "chain rule",
                "objectives": [
                    {"id": "LO1", "text": "x", "prerequisites": ["LO_MISSING"]},
                ],
                "sequence": ["LO1"],
            }
        )


def _scene(idx: int, beat: str, dur: float, **kw: object) -> dict:
    return {
        "scene_id": f"scene_{idx:02d}",
        "beat_type": beat,
        "target_duration_seconds": dur,
        "visual_intent": f"visual for scene {idx}",
        "narration_intent": f"narration for scene {idx}",
        **kw,
    }


def test_storyboard_happy_path() -> None:
    sb = Storyboard.model_validate(
        {
            **_meta("storyboard"),
            "topic": "chain rule",
            "total_duration_seconds": 180.0,
            "scenes": [
                _scene(1, "hook", 15.0),
                _scene(2, "define", 45.0, learning_objective_id="LO1"),
                _scene(3, "example", 60.0, learning_objective_id="LO2"),
                _scene(4, "recap", 60.0),
            ],
            "palette": {"bg": "#000", "fg": "#fff"},
            "voice_id": "21m00Tcm4TlvDq8ikWAM",
        }
    )
    assert sb.scenes[0].beat_type == "hook"


def test_storyboard_requires_consecutive_scene_ids() -> None:
    with pytest.raises(ValidationError):
        Storyboard.model_validate(
            {
                **_meta("storyboard"),
                "topic": "chain rule",
                "total_duration_seconds": 120.0,
                "scenes": [
                    _scene(1, "define", 60.0),
                    _scene(3, "example", 60.0),
                ],
                "palette": {"bg": "#000"},
                "voice_id": "v1",
            }
        )


def test_storyboard_rejects_duration_mismatch() -> None:
    with pytest.raises(ValidationError):
        Storyboard.model_validate(
            {
                **_meta("storyboard"),
                "topic": "chain rule",
                "total_duration_seconds": 180.0,
                "scenes": [_scene(1, "define", 30.0)],
                "palette": {"bg": "#000"},
                "voice_id": "v1",
            }
        )


def test_storyboard_hook_must_be_first() -> None:
    with pytest.raises(ValidationError):
        Storyboard.model_validate(
            {
                **_meta("storyboard"),
                "topic": "chain rule",
                "total_duration_seconds": 60.0,
                "scenes": [
                    _scene(1, "define", 30.0),
                    _scene(2, "hook", 30.0),
                ],
                "palette": {"bg": "#000"},
                "voice_id": "v1",
            }
        )


def test_storyboard_scene_model_strips_whitespace() -> None:
    sb = SceneBeat.model_validate(
        {
            "scene_id": "scene_01",
            "beat_type": "hook",
            "target_duration_seconds": 12.0,
            "visual_intent": "  show curve  ",
            "narration_intent": "  motivate  ",
        }
    )
    assert sb.visual_intent == "show curve"


def test_job_state_round_trip() -> None:
    payload = {
        **_meta("orchestrator"),
        "job_id": str(uuid4()),
        "created_at": "2026-04-20T12:00:00Z",
        "user_prompt": "explain derivatives",
        "stages": [
            StageStatus(name="intake", status="pending").model_dump(),
            StageStatus(name="curriculum", status="pending").model_dump(),
            StageStatus(name="storyboard", status="pending").model_dump(),
        ],
        "current_stage": "intake",
        "terminal": False,
    }
    parsed = JobState.model_validate(payload)
    assert parsed.stages[0].name == "intake"
    assert parsed.terminal is False


def test_extra_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        IntakeResult.model_validate(
            {
                **_meta("intake"),
                "topic": "chain rule",
                "domain": "calculus",
                "audience_level": "undergrad",
                "target_length_seconds": 180,
                "extra_garbage": "nope",
            }
        )
