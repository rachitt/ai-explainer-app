"""Pydantic message schemas for Pedagogica agents."""

from pedagogica_schemas.audio import AudioClip, WordTiming
from pedagogica_schemas.base import BaseMessage
from pedagogica_schemas.critique import CritiqueIssue, ScriptCritique
from pedagogica_schemas.curriculum import CurriculumPlan, LearningObjective, Misconception
from pedagogica_schemas.intake import IntakeResult
from pedagogica_schemas.job import JobState, StageStatus
from pedagogica_schemas.layout import ElementPlacement, LayoutResult
from pedagogica_schemas.chalk_code import ChalkCode, CompileResult
from pedagogica_schemas.registry import SCHEMA_REGISTRY
from pedagogica_schemas.scene_spec import SceneAnimation, SceneElement, SceneSpec
from pedagogica_schemas.script import Script, ScriptMarker
from pedagogica_schemas.storyboard import SceneBeat, Storyboard
from pedagogica_schemas.sync import AnimationTiming, SyncPlan

__all__ = [
    "SCHEMA_REGISTRY",
    "AnimationTiming",
    "AudioClip",
    "BaseMessage",
    "CompileResult",
    "CritiqueIssue",
    "CurriculumPlan",
    "ElementPlacement",
    "IntakeResult",
    "JobState",
    "LayoutResult",
    "LearningObjective",
    "ChalkCode",
    "Misconception",
    "SceneAnimation",
    "SceneBeat",
    "SceneElement",
    "SceneSpec",
    "Script",
    "ScriptCritique",
    "ScriptMarker",
    "StageStatus",
    "Storyboard",
    "SyncPlan",
    "WordTiming",
]
