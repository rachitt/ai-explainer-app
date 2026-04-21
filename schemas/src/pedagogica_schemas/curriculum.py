from typing import Self

from pydantic import BaseModel, Field, model_validator

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

    @model_validator(mode="after")
    def _sequence_and_prereqs_consistent(self) -> Self:
        ids = {lo.id for lo in self.objectives}

        for lo in self.objectives:
            missing = [p for p in lo.prerequisites if p not in ids]
            if missing:
                raise ValueError(
                    f"objective {lo.id} has unknown prerequisites: {missing}"
                )

        seen: set[str] = set()
        for sid in self.sequence:
            if sid not in ids:
                raise ValueError(f"sequence references unknown objective id: {sid}")
            lo = next(o for o in self.objectives if o.id == sid)
            missing = [p for p in lo.prerequisites if p not in seen]
            if missing:
                raise ValueError(
                    f"objective {sid} appears before its prerequisites {missing}"
                )
            seen.add(sid)

        return self
