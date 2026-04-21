from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from pedagogica_schemas.base import BaseMessage, StrictModel

StageName = Literal[
    "intake",
    "curriculum",
    "storyboard",
    "script",
    "script_critic",
    "visual_planner",
    "layout",
    "manim_code",
    "compile",
    "manim_repair",
    "tts",
    "sync",
    "editor",
    "subtitle",
    "pedagogical_critic",
    "visual_critic",
    "factual_verifier",
    "accessibility_auditor",
]

StageStatusName = Literal["pending", "in_progress", "complete", "failed", "skipped"]


class StageStatus(StrictModel):
    name: StageName
    status: StageStatusName
    started_at: datetime | None = None
    completed_at: datetime | None = None
    artifact_path: str | None = None
    cost_usd: float = Field(default=0.0, ge=0.0)
    token_counts: dict[str, int] = Field(default_factory=dict)


class JobState(BaseMessage):
    """Authoritative orchestrator state. Persisted on every stage transition (§8)."""

    job_id: UUID
    created_at: datetime
    user_prompt: str = Field(min_length=1)
    skills_pinned: dict[str, str] = Field(default_factory=dict)
    models_default: dict[str, str] = Field(default_factory=dict)
    stages: list[StageStatus] = Field(min_length=1)
    current_stage: StageName | None = None
    terminal: bool = False
    final_artifact_paths: dict[str, str] = Field(default_factory=dict)
