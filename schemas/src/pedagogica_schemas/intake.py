from typing import Literal

from pydantic import Field

from pedagogica_schemas.base import BaseMessage

Domain = Literal["calculus", "linalg", "prob", "stats", "discrete", "algebra"]
AudienceLevel = Literal["elementary", "highschool", "undergrad", "graduate"]


class IntakeResult(BaseMessage):
    schema_version: str = "0.1.0"
    topic: str
    domain: Domain
    audience_level: AudienceLevel
    target_length_seconds: int
    style_hints: list[str] = Field(default_factory=list)
    clarification_needed: bool = False
    clarification_question: str | None = None
