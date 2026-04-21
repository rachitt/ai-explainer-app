from typing import Literal

from pydantic import Field, model_validator

from pedagogica_schemas.base import BaseMessage, StrictModel

BeatType = Literal["hook", "define", "motivate", "example", "generalize", "recap"]


class SceneBeat(StrictModel):
    scene_id: str = Field(pattern=r"^scene_\d{2,}$")
    beat_type: BeatType
    target_duration_seconds: float = Field(gt=0)
    learning_objective_id: str | None = None
    visual_intent: str = Field(min_length=1)
    narration_intent: str = Field(min_length=1)
    required_skills: list[str] = Field(default_factory=list)


class Storyboard(BaseMessage):
    """The master plan. Output of the Storyboard agent (ARCHITECTURE.md §5.3)."""

    topic: str = Field(min_length=1)
    total_duration_seconds: float = Field(gt=0)
    scenes: list[SceneBeat] = Field(min_length=1)
    palette: dict[str, str] = Field(min_length=1)
    voice_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def _scene_constraints(self) -> "Storyboard":
        ids = [s.scene_id for s in self.scenes]
        if len(set(ids)) != len(ids):
            raise ValueError(f"duplicate scene_id in scenes: {ids}")
        expected = [f"scene_{i:02d}" for i in range(1, len(self.scenes) + 1)]
        if ids != expected:
            raise ValueError(
                "scene_ids must be consecutive starting at scene_01; "
                f"got {ids}, expected {expected}"
            )
        hook_count = sum(1 for s in self.scenes if s.beat_type == "hook")
        recap_count = sum(1 for s in self.scenes if s.beat_type == "recap")
        if hook_count > 1:
            raise ValueError(f"at most one hook beat; got {hook_count}")
        if recap_count > 1:
            raise ValueError(f"at most one recap beat; got {recap_count}")
        if hook_count == 1 and self.scenes[0].beat_type != "hook":
            raise ValueError("hook beat must be scene_01")
        if recap_count == 1 and self.scenes[-1].beat_type != "recap":
            raise ValueError("recap beat must be the final scene")

        total = sum(s.target_duration_seconds for s in self.scenes)
        tol = 0.10 * self.total_duration_seconds
        if abs(total - self.total_duration_seconds) > tol:
            raise ValueError(
                f"scene durations ({total:.1f}s) deviate more than 10% "
                f"from total_duration_seconds ({self.total_duration_seconds:.1f}s)"
            )
        return self
