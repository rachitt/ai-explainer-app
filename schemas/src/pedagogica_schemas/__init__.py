"""Pydantic message schemas for Pedagogica agents."""

from pedagogica_schemas.audio import AudioClip, WordTiming
from pedagogica_schemas.base import BaseMessage
from pedagogica_schemas.curriculum import CurriculumPlan, LearningObjective, Misconception
from pedagogica_schemas.intake import IntakeResult
from pedagogica_schemas.job import JobState, StageStatus
from pedagogica_schemas.layout import ElementPlacement, LayoutResult
from pedagogica_schemas.manim_code import CompileResult, ManimCode
from pedagogica_schemas.scene_spec import SceneAnimation, SceneElement, SceneSpec
from pedagogica_schemas.script import Script, ScriptMarker
from pedagogica_schemas.storyboard import SceneBeat, Storyboard
from pedagogica_schemas.sync import AnimationTiming, SyncPlan

__all__ = [
    "AnimationTiming",
    "AudioClip",
    "BaseMessage",
    "CompileResult",
    "CurriculumPlan",
    "ElementPlacement",
    "IntakeResult",
    "JobState",
    "LayoutResult",
    "LearningObjective",
    "ManimCode",
    "Misconception",
    "SceneAnimation",
    "SceneBeat",
    "SceneElement",
    "SceneSpec",
    "Script",
    "ScriptMarker",
    "StageStatus",
    "Storyboard",
    "SyncPlan",
    "WordTiming",
]
