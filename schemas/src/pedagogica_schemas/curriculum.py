from pydantic import Field, model_validator

from pedagogica_schemas.base import BaseMessage, StrictModel


class LearningObjective(StrictModel):
    id: str = Field(pattern=r"^LO\d+$")
    text: str = Field(min_length=1)
    prerequisites: list[str] = Field(default_factory=list)


class Misconception(StrictModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    preempt_strategy: str = Field(min_length=1)


class CurriculumPlan(BaseMessage):
    """Pedagogical plan. Output of the Curriculum agent (ARCHITECTURE.md §5.2)."""

    topic: str = Field(min_length=1)
    objectives: list[LearningObjective] = Field(min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    misconceptions: list[Misconception] = Field(default_factory=list)
    worked_examples: list[str] = Field(default_factory=list)
    sequence: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def _sequence_is_permutation_of_objectives(self) -> "CurriculumPlan":
        obj_ids = [lo.id for lo in self.objectives]
        if sorted(obj_ids) != sorted(self.sequence):
            raise ValueError(
                f"sequence must be a permutation of objective ids; "
                f"objectives={sorted(obj_ids)}, sequence={sorted(self.sequence)}"
            )
        obj_id_set = set(obj_ids)
        for lo in self.objectives:
            for prereq in lo.prerequisites:
                if prereq not in obj_id_set:
                    raise ValueError(
                        f"{lo.id}.prerequisites references unknown objective id {prereq!r}"
                    )
        placed: set[str] = set()
        for lo_id in self.sequence:
            lo = next(o for o in self.objectives if o.id == lo_id)
            for prereq in lo.prerequisites:
                if prereq not in placed:
                    raise ValueError(
                        f"sequence violates prerequisites: {lo_id} placed before {prereq}"
                    )
            placed.add(lo_id)
        return self
