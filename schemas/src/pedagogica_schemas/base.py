from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class BaseMessage(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
        str_strip_whitespace=True,
        protected_namespaces=(),
    )

    trace_id: UUID
    span_id: UUID
    parent_span_id: UUID | None = None
    timestamp: datetime = Field(default_factory=_utc_now)
    producer: str
    schema_version: str
