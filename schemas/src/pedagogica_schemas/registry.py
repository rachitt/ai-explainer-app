from pedagogica_schemas.audio import AudioClip
from pedagogica_schemas.base import BaseMessage
from pedagogica_schemas.critique import ScriptCritique
from pedagogica_schemas.curriculum import CurriculumPlan
from pedagogica_schemas.intake import IntakeResult
from pedagogica_schemas.job import JobState
from pedagogica_schemas.layout import LayoutResult
from pedagogica_schemas.chalk_code import ChalkCode, CompileResult
from pedagogica_schemas.scene_spec import SceneSpec
from pedagogica_schemas.script import Script
from pedagogica_schemas.storyboard import Storyboard
from pedagogica_schemas.sync import SyncPlan

SCHEMA_REGISTRY: dict[str, type[BaseMessage]] = {
    "AudioClip": AudioClip,
    "CompileResult": CompileResult,
    "CurriculumPlan": CurriculumPlan,
    "IntakeResult": IntakeResult,
    "JobState": JobState,
    "LayoutResult": LayoutResult,
    "ChalkCode": ChalkCode,
    "SceneSpec": SceneSpec,
    "Script": Script,
    "ScriptCritique": ScriptCritique,
    "Storyboard": Storyboard,
    "SyncPlan": SyncPlan,
}
