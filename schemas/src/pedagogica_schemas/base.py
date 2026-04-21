from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    """Base for all Pedagogica models — reject unknown fields, strip whitespace."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class BaseMessage(StrictModel):
    """Every inter-agent message carries trace metadata. See ARCHITECTURE.md §5."""

    trace_id: UUID
    span_id: UUID
    parent_span_id: UUID | None = None
    timestamp: datetime = Field(default_factory=_utc_now)
    producer: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
