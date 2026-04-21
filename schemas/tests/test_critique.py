from uuid import uuid4

import pytest
from pedagogica_schemas import SCHEMA_REGISTRY, CritiqueIssue, ScriptCritique
from pydantic import ValidationError


def _meta() -> dict:
    return {
        "trace_id": str(uuid4()),
        "span_id": str(uuid4()),
        "producer": "script-critic",
        "schema_version": "0.1.0",
    }


def _all_dims(v: float = 4.0) -> dict[str, float]:
    return {
        "narration_style": v,
        "pacing": v,
        "pedagogical_alignment": v,
        "marker_quality": v,
    }


def test_registry_has_script_critique() -> None:
    assert "ScriptCritique" in SCHEMA_REGISTRY


def test_script_critique_round_trip() -> None:
    payload = {
        **_meta(),
        "scene_id": "scene_02",
        "script_span_id": str(uuid4()),
        "overall_score": 4.1,
        "dimension_scores": _all_dims(),
        "issues": [
            CritiqueIssue(
                severity="warning",
                dimension="pacing",
                word_index=12,
                message="no pause after the landing sentence",
                suggestion="insert a 0.8s pause marker after word 12",
            ).model_dump()
        ],
        "summary": "narration lands but pacing is flat",
        "blocking": False,
    }
    parsed = ScriptCritique.model_validate(payload)
    back = ScriptCritique.model_validate_json(parsed.model_dump_json())
    assert back == parsed


def test_script_critique_rejects_missing_dimension() -> None:
    scores = _all_dims()
    scores.pop("pacing")
    with pytest.raises(ValidationError):
        ScriptCritique.model_validate(
            {
                **_meta(),
                "scene_id": "scene_01",
                "script_span_id": str(uuid4()),
                "overall_score": 3.5,
                "dimension_scores": scores,
                "summary": "missing dim",
            }
        )


def test_script_critique_rejects_unknown_dimension() -> None:
    scores = _all_dims()
    scores["vibes"] = 5.0
    with pytest.raises(ValidationError):
        ScriptCritique.model_validate(
            {
                **_meta(),
                "scene_id": "scene_01",
                "script_span_id": str(uuid4()),
                "overall_score": 3.5,
                "dimension_scores": scores,
                "summary": "extra dim",
            }
        )


def test_script_critique_rejects_score_out_of_range() -> None:
    with pytest.raises(ValidationError):
        ScriptCritique.model_validate(
            {
                **_meta(),
                "scene_id": "scene_01",
                "script_span_id": str(uuid4()),
                "overall_score": 6.0,
                "dimension_scores": _all_dims(),
                "summary": "over-scored",
            }
        )


def test_script_critique_blocking_requires_blocker_issue() -> None:
    with pytest.raises(ValidationError):
        ScriptCritique.model_validate(
            {
                **_meta(),
                "scene_id": "scene_01",
                "script_span_id": str(uuid4()),
                "overall_score": 2.0,
                "dimension_scores": _all_dims(1.0),
                "issues": [
                    CritiqueIssue(
                        severity="warning",
                        dimension="narration_style",
                        message="weak opening",
                        suggestion="lead with the question",
                    ).model_dump()
                ],
                "summary": "inconsistent blocking flag",
                "blocking": True,
            }
        )


def test_script_critique_blocking_accepts_blocker_issue() -> None:
    parsed = ScriptCritique.model_validate(
        {
            **_meta(),
            "scene_id": "scene_01",
            "script_span_id": str(uuid4()),
            "overall_score": 1.5,
            "dimension_scores": _all_dims(1.0),
            "issues": [
                CritiqueIssue(
                    severity="blocker",
                    dimension="pedagogical_alignment",
                    message="narration contradicts the storyboard beat",
                    suggestion="regenerate the script against the beat's narration_intent",
                ).model_dump()
            ],
            "summary": "off-beat narration",
            "blocking": True,
        }
    )
    assert parsed.blocking is True


def test_script_critique_rejects_unknown_top_level_field() -> None:
    with pytest.raises(ValidationError):
        ScriptCritique.model_validate(
            {
                **_meta(),
                "scene_id": "scene_01",
                "script_span_id": str(uuid4()),
                "overall_score": 3.0,
                "dimension_scores": _all_dims(),
                "summary": "ok",
                "stray": "nope",
            }
        )
