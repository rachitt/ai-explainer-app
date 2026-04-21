from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from pedagogica_schemas.base import BaseMessage

StageStatusLiteral = Literal["pending", "in_progress", "complete", "failed", "skipped"]


class StageStatus(BaseModel):
    name: str
    status: StageStatusLiteral
    started_at: datetime | None = None
    completed_at: datetime | None = None
    artifact_path: str | None = None
    cost_usd: float = 0.0
    token_counts: dict[str, int] = Field(default_factory=dict)


class JobState(BaseMessage):
    schema_version: str = "0.1.0"
    job_id: UUID
    created_at: datetime
    user_prompt: str
    skills_pinned: dict[str, str] = Field(default_factory=dict)
    models_default: dict[str, str] = Field(default_factory=dict)
    stages: list[StageStatus]
    current_stage: str | None = None
    terminal: bool = False
    final_artifact_paths: dict[str, str] = Field(default_factory=dict)
