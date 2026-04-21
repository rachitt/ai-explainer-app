from typing import Any, Literal

from pydantic import BaseModel, Field

from pedagogica_schemas.base import BaseMessage

ElementType = Literal["math", "text", "shape", "graph", "axes", "arrow", "label", "image"]
AnimationOp = Literal["write", "create", "transform", "fade_in", "fade_out", "move_to", "highlight"]


class SceneElement(BaseModel):
    id: str
    type: ElementType
    content: str
    properties: dict[str, Any] = Field(default_factory=dict)


class SceneAnimation(BaseModel):
    id: str
    op: AnimationOp
    target_ids: list[str]
    duration_seconds: float
    run_after: str | None = None


class SceneSpec(BaseMessage):
    schema_version: str = "0.1.0"
    scene_id: str
    elements: list[SceneElement]
    animations: list[SceneAnimation]
    camera: dict[str, Any] = Field(default_factory=dict)
