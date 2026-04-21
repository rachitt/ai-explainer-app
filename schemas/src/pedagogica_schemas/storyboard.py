from typing import Literal

from pydantic import BaseModel, Field

from pedagogica_schemas.base import BaseMessage

BeatType = Literal["hook", "define", "motivate", "example", "generalize", "recap"]


class SceneBeat(BaseModel):
    scene_id: str
    beat_type: BeatType
    target_duration_seconds: float
    learning_objective_id: str | None = None
    visual_intent: str
    narration_intent: str
    required_skills: list[str] = Field(default_factory=list)


class Storyboard(BaseMessage):
    schema_version: str = "0.1.0"
    topic: str
    total_duration_seconds: float
    scenes: list[SceneBeat]
    palette: dict[str, str] = Field(default_factory=dict)
    voice_id: str
