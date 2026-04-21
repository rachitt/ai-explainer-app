from pydantic import BaseModel, Field

from pedagogica_schemas.base import BaseMessage


class ElementPlacement(BaseModel):
    id: str
    position: tuple[float, float]
    scale: float
    z_order: int
    font_size: float | None = None


class LayoutResult(BaseMessage):
    schema_version: str = "0.1.0"
    scene_id: str
    placements: list[ElementPlacement]
    overlap_warnings: list[str] = Field(default_factory=list)
    frame_bounds_ok: bool
