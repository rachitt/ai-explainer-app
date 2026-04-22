from typing import Literal, Self

from pydantic import Field, model_validator

from pedagogica_schemas.base import BaseMessage

Domain = Literal[
    "calculus", "linalg", "prob", "stats", "discrete", "algebra",
    "physics", "circuits", "chemistry", "coding",
]
AudienceLevel = Literal["elementary", "highschool", "undergrad", "graduate"]


class IntakeResult(BaseMessage):
    schema_version: str = "0.1.0"
    topic: str
    domain: Domain
    audience_level: AudienceLevel
    target_length_seconds: int = Field(ge=30, le=3600)
    style_hints: list[str] = Field(default_factory=list)
    clarification_needed: bool = False
    clarification_question: str | None = None

    @model_validator(mode="after")
    def _clarification_consistency(self) -> Self:
        if self.clarification_needed and not self.clarification_question:
            raise ValueError(
                "clarification_question must be provided when clarification_needed is true"
            )
        if not self.clarification_needed and self.clarification_question:
            raise ValueError(
                "clarification_question must be null when clarification_needed is false"
            )
        return self
