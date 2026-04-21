from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pedagogica_schemas.base import BaseMessage

CritiqueDimension = Literal[
    "narration_style",
    "pacing",
    "pedagogical_alignment",
    "marker_quality",
]

CritiqueSeverity = Literal["info", "warning", "blocker"]

_REQUIRED_DIMENSIONS: frozenset[CritiqueDimension] = frozenset(
    {"narration_style", "pacing", "pedagogical_alignment", "marker_quality"}
)


class CritiqueIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    severity: CritiqueSeverity
    dimension: CritiqueDimension
    word_index: int | None = None
    message: str = Field(min_length=1)
    suggestion: str = Field(min_length=1)


class ScriptCritique(BaseMessage):
    schema_version: str = "0.1.0"
    scene_id: str
    script_span_id: UUID
    overall_score: float = Field(ge=0.0, le=5.0)
    dimension_scores: dict[CritiqueDimension, float] = Field(default_factory=dict)
    issues: list[CritiqueIssue] = Field(default_factory=list)
    summary: str = Field(min_length=1)
    blocking: bool = False

    @model_validator(mode="after")
    def _dimensions_complete_and_in_range(self) -> Self:
        present = set(self.dimension_scores)
        missing = _REQUIRED_DIMENSIONS - present
        if missing:
            raise ValueError(f"dimension_scores missing required keys: {sorted(missing)}")
        extra = present - _REQUIRED_DIMENSIONS
        if extra:
            raise ValueError(f"dimension_scores has unknown keys: {sorted(extra)}")
        for dim, score in self.dimension_scores.items():
            if not 0.0 <= score <= 5.0:
                raise ValueError(f"dimension_scores[{dim!r}] = {score} outside [0.0, 5.0]")

        if self.blocking and not any(i.severity == "blocker" for i in self.issues):
            raise ValueError("blocking is true but no issue has severity='blocker'")

        return self
