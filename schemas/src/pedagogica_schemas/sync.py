from pydantic import BaseModel, Field

from pedagogica_schemas.base import BaseMessage


class AnimationTiming(BaseModel):
    animation_id: str
    start_seconds: float
    run_time_seconds: float
    wait_after_seconds: float
    anchored_word_indices: list[int] = Field(default_factory=list)


class SyncPlan(BaseMessage):
    schema_version: str = "0.1.0"
    scene_id: str
    timings: list[AnimationTiming]
    total_scene_duration: float
    audio_offset_seconds: float
    drift_seconds: float
