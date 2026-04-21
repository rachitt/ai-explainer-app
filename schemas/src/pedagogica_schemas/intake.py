from typing import Literal

from pydantic import Field, model_validator

from pedagogica_schemas.base import BaseMessage

Domain = Literal[
    "calculus",
    "linalg",
    "prob",
    "mechanics",
    "em",
    "quantum",
    "chem",
    "bio",
    "algo",
    "ml",
    "econ",
]

AudienceLevel = Literal["elementary", "highschool", "undergrad", "graduate"]


class IntakeResult(BaseMessage):
    """Normalized user prompt. Output of the Intake agent (ARCHITECTURE.md §5.1)."""

    topic: str = Field(min_length=1)
    domain: Domain
    audience_level: AudienceLevel
    target_length_seconds: int = Field(ge=60, le=600)
    style_hints: list[str] = Field(default_factory=list)
    clarification_needed: bool = False
    clarification_question: str | None = None

    @model_validator(mode="after")
    def _clarification_consistency(self) -> "IntakeResult":
        if self.clarification_needed and not self.clarification_question:
            raise ValueError(
                "clarification_question required when clarification_needed is true"
            )
        if not self.clarification_needed and self.clarification_question is not None:
            raise ValueError(
                "clarification_question must be null when clarification_needed is false"
            )
        return self
