from typing import Literal

from pydantic import Field

from pedagogica_schemas.base import BaseMessage

ErrorClassification = Literal[
    "import_error",
    "latex_error",
    "geometry_error",
    "timing_error",
    "memory_error",
    "timeout",
    "other",
]


class ManimCode(BaseMessage):
    schema_version: str = "0.1.0"
    scene_id: str
    code: str
    scene_class_name: str
    skills_loaded: list[str] = Field(default_factory=list)


class CompileResult(BaseMessage):
    schema_version: str = "0.1.0"
    scene_id: str
    success: bool
    attempt_number: int
    video_path: str | None = None
    frame_count: int | None = None
    duration_seconds: float | None = None
    stderr: str | None = None
    stdout_tail: str | None = None
    error_classification: ErrorClassification | None = None
