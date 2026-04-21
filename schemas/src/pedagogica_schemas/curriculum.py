from pydantic import BaseModel, Field

from pedagogica_schemas.base import BaseMessage


class LearningObjective(BaseModel):
    id: str
    text: str
    prerequisites: list[str] = Field(default_factory=list)


class Misconception(BaseModel):
    id: str
    description: str
    preempt_strategy: str


class CurriculumPlan(BaseMessage):
    schema_version: str = "0.1.0"
    topic: str
    objectives: list[LearningObjective]
    prerequisites: list[str] = Field(default_factory=list)
    misconceptions: list[Misconception] = Field(default_factory=list)
    worked_examples: list[str] = Field(default_factory=list)
    sequence: list[str]
