from pedagogica_schemas.base import BaseMessage
from pedagogica_schemas.curriculum import CurriculumPlan
from pedagogica_schemas.intake import IntakeResult
from pedagogica_schemas.job import JobState
from pedagogica_schemas.storyboard import Storyboard

SCHEMA_REGISTRY: dict[str, type[BaseMessage]] = {
    "IntakeResult": IntakeResult,
    "CurriculumPlan": CurriculumPlan,
    "Storyboard": Storyboard,
    "JobState": JobState,
}
