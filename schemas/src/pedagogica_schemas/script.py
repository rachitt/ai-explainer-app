from typing import Literal

from pydantic import BaseModel, Field

from pedagogica_schemas.base import BaseMessage

MarkerType = Literal["show", "highlight", "pause", "transition"]


class ScriptMarker(BaseModel):
    word_index: int
    marker_type: MarkerType
    ref: str


class Script(BaseMessage):
    schema_version: str = "0.1.0"
    scene_id: str
    text: str
    words: list[str]
    markers: list[ScriptMarker] = Field(default_factory=list)
    estimated_duration_seconds: float
