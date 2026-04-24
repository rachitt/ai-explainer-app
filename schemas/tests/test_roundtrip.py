from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from pedagogica_schemas import (
    AnimationTiming,
    AudioClip,
    BaseMessage,
    CompileResult,
    CurriculumPlan,
    ElementPlacement,
    IntakeResult,
    JobState,
    LayoutResult,
    LearningObjective,
    ChalkCode,
    Misconception,
    SceneAnimation,
    SceneBeat,
    SceneElement,
    SceneSpec,
    Script,
    ScriptMarker,
    StageStatus,
    Storyboard,
    SyncPlan,
    WordTiming,
)
from pydantic import ValidationError


def _base() -> dict[str, Any]:
    return {
        "trace_id": uuid4(),
        "span_id": uuid4(),
        "producer": "test",
        "schema_version": "0.1.0",
    }


def _intake() -> IntakeResult:
    return IntakeResult(
        **_base(),
        topic="chain rule",
        hook_question="why does the chain rule need an inner derivative?",
        domain="calculus",
        audience_level="undergrad",
        target_length_seconds=180,
        style_hints=["3blue1brown", "dark-bg"],
    )


def _curriculum() -> CurriculumPlan:
    return CurriculumPlan(
        **_base(),
        topic="chain rule",
        objectives=[
            LearningObjective(id="LO1", text="compose derivatives", prerequisites=[]),
            LearningObjective(id="LO2", text="apply to trig", prerequisites=["LO1"]),
        ],
        prerequisites=["derivative"],
        misconceptions=[
            Misconception(
                id="M1",
                description="thinks d/dx[f(g(x))] = f'(g'(x))",
                preempt_strategy="walk through composition slowly",
            )
        ],
        worked_examples=["d/dx sin(x^2)"],
        sequence=["LO1", "LO2"],
    )


def _storyboard() -> Storyboard:
    return Storyboard(
        **_base(),
        topic="chain rule",
        hook_question="why does the chain rule need an inner derivative?",
        total_duration_seconds=15.0,
        scenes=[
            SceneBeat(
                scene_id="scene_01",
                beat_type="hook",
                target_duration_seconds=15.0,
                learning_objective_id="LO1",
                visual_intent="show f(g(x)) unfolding",
                narration_intent="hook them on composition",
                required_skills=["manim-calculus-patterns"],
            )
        ],
        palette={"primary": "#ffcc00"},
        voice_id="voice_abc",
    )


def _script() -> Script:
    return Script(
        **_base(),
        scene_id="scene_01",
        text="The chain rule says multiply.",
        words=["The", "chain", "rule", "says", "multiply."],
        markers=[ScriptMarker(word_index=1, marker_type="show", ref="eq.chain")],
        estimated_duration_seconds=4.0,
    )


def _scene_spec() -> SceneSpec:
    return SceneSpec(
        **_base(),
        scene_id="scene_01",
        elements=[
            SceneElement(
                id="eq.f",
                type="math",
                content=r"f(x)=x^2",
                properties={"color": "#ffffff"},
            )
        ],
        animations=[
            SceneAnimation(
                id="a1",
                op="write",
                target_ids=["eq.f"],
                duration_seconds=0.6,
                run_after=None,
            )
        ],
    )


def _layout() -> LayoutResult:
    return LayoutResult(
        **_base(),
        scene_id="scene_01",
        placements=[
            ElementPlacement(id="eq.f", position=(0.0, 1.0), scale=1.0, z_order=1, font_size=48.0)
        ],
        overlap_warnings=[],
        frame_bounds_ok=True,
    )


def _chalk_code() -> ChalkCode:
    return ChalkCode(
        **_base(),
        scene_id="scene_01",
        code="from chalk import Scene\n\nclass S(Scene):\n    def construct(self): pass\n",
        scene_class_name="S",
        skills_loaded=["chalk-primitives"],
    )


def _compile_result() -> CompileResult:
    return CompileResult(
        **_base(),
        scene_id="scene_01",
        success=True,
        attempt_number=1,
        video_path="/tmp/s.mp4",
        frame_count=450,
        duration_seconds=15.0,
    )


def _audio_clip() -> AudioClip:
    return AudioClip(
        **_base(),
        scene_id="scene_01",
        audio_path="/tmp/s.mp3",
        total_duration_seconds=4.0,
        word_timings=[
            WordTiming(word="The", start_seconds=0.0, end_seconds=0.2, char_start=0, char_end=3)
        ],
        voice_id="voice_abc",
        model_id="eleven_multilingual_v2",
        char_count=28,
    )


def _sync_plan() -> SyncPlan:
    return SyncPlan(
        **_base(),
        scene_id="scene_01",
        timings=[
            AnimationTiming(
                animation_id="a1",
                start_seconds=0.0,
                run_time_seconds=0.6,
                wait_after_seconds=0.2,
                anchored_word_indices=[1],
            )
        ],
        total_scene_duration=4.0,
        audio_offset_seconds=0.0,
        drift_seconds=0.05,
    )


def _job_state() -> JobState:
    now = datetime.now(UTC)
    return JobState(
        **_base(),
        job_id=uuid4(),
        created_at=now,
        user_prompt="explain chain rule",
        skills_pinned={"manim-primitives": "1.0.0"},
        models_default={"manim-code": "claude-opus-4-7"},
        stages=[
            StageStatus(
                name="intake",
                status="complete",
                started_at=now,
                completed_at=now,
                artifact_path="01_intake.json",
                cost_usd=0.0,
                token_counts={"input": 100, "output": 50},
            )
        ],
        current_stage="curriculum",
        terminal=False,
    )


FACTORIES: list[tuple[type[BaseMessage], Callable[[], BaseMessage]]] = [
    (IntakeResult, _intake),
    (CurriculumPlan, _curriculum),
    (Storyboard, _storyboard),
    (Script, _script),
    (SceneSpec, _scene_spec),
    (LayoutResult, _layout),
    (ChalkCode, _chalk_code),
    (CompileResult, _compile_result),
    (AudioClip, _audio_clip),
    (SyncPlan, _sync_plan),
    (JobState, _job_state),
]


@pytest.mark.parametrize("cls,factory", FACTORIES, ids=[c.__name__ for c, _ in FACTORIES])
def test_roundtrip(cls: type[BaseMessage], factory: Callable[[], BaseMessage]) -> None:
    inst = factory()
    back = cls.model_validate_json(inst.model_dump_json())
    assert back == inst


@pytest.mark.parametrize("cls,factory", FACTORIES, ids=[c.__name__ for c, _ in FACTORIES])
def test_extra_top_level_field_forbidden(
    cls: type[BaseMessage], factory: Callable[[], BaseMessage]
) -> None:
    raw = factory().model_dump(mode="json")
    raw["unexpected_top_level_field"] = "nope"
    with pytest.raises(ValidationError):
        cls.model_validate(raw)


@pytest.mark.parametrize("cls,factory", FACTORIES, ids=[c.__name__ for c, _ in FACTORIES])
def test_schema_version_default(cls: type[BaseMessage], factory: Callable[[], BaseMessage]) -> None:
    assert factory().schema_version == "0.1.0"
