from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pedagogica_schemas.base import BaseMessage

BeatType = Literal["hook", "define", "motivate", "example", "generalize", "recap"]

_DURATION_TOLERANCE_S = 0.5


class SceneBeat(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scene_id: str
    beat_type: BeatType
    target_duration_seconds: float = Field(gt=0)
    learning_objective_id: str | None = None
    visual_intent: str = Field(min_length=1)
    narration_intent: str = Field(min_length=1)
    required_skills: list[str] = Field(default_factory=list)


class Storyboard(BaseMessage):
    schema_version: str = "0.1.0"
    topic: str
    total_duration_seconds: float = Field(gt=0)
    scenes: list[SceneBeat] = Field(min_length=1)
    palette: dict[str, str] = Field(default_factory=dict)
    voice_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def _scenes_consistent(self) -> Self:
        for idx, scene in enumerate(self.scenes, start=1):
            expected = f"scene_{idx:02d}"
            if scene.scene_id != expected:
                raise ValueError(
                    f"scene_id at position {idx} is {scene.scene_id!r}, expected {expected!r} (must be consecutive scene_NN)"
                )

        total = sum(s.target_duration_seconds for s in self.scenes)
        if abs(total - self.total_duration_seconds) > _DURATION_TOLERANCE_S:
            raise ValueError(
                f"sum of scene durations {total:.2f}s does not match total_duration_seconds {self.total_duration_seconds:.2f}s"
            )

        hook_indices = [i for i, s in enumerate(self.scenes) if s.beat_type == "hook"]
        if hook_indices and hook_indices[0] != 0:
            raise ValueError("hook beat must be the first scene if present")
        if len(hook_indices) > 1:
            raise ValueError("at most one hook beat is allowed")

        return self
