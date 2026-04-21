from typing import Any
from uuid import uuid4

import pytest
from pedagogica_schemas import BaseMessage
from pydantic import ValidationError


def _kwargs() -> dict[str, Any]:
    return {
        "trace_id": uuid4(),
        "span_id": uuid4(),
        "producer": "intake",
        "schema_version": "0.1.0",
    }


def test_minimal_instance() -> None:
    msg = BaseMessage(**_kwargs())
    assert msg.producer == "intake"
    assert msg.parent_span_id is None
    assert msg.schema_version == "0.1.0"


def test_timestamp_default_is_tz_aware_utc() -> None:
    msg = BaseMessage(**_kwargs())
    assert msg.timestamp.tzinfo is not None
    offset = msg.timestamp.utcoffset()
    assert offset is not None
    assert offset.total_seconds() == 0


def test_missing_required_field_raises() -> None:
    with pytest.raises(ValidationError):
        BaseMessage(span_id=uuid4(), producer="x", schema_version="0.1.0")  # type: ignore[call-arg]


def test_extra_fields_forbidden() -> None:
    kwargs = _kwargs()
    kwargs["unexpected"] = "nope"
    with pytest.raises(ValidationError):
        BaseMessage(**kwargs)


def test_producer_whitespace_stripped() -> None:
    kwargs = _kwargs()
    kwargs["producer"] = "  intake  "
    msg = BaseMessage(**kwargs)
    assert msg.producer == "intake"


def test_json_roundtrip() -> None:
    msg = BaseMessage(**_kwargs())
    back = BaseMessage.model_validate_json(msg.model_dump_json())
    assert back == msg


def test_parent_span_id_accepted() -> None:
    kwargs = _kwargs()
    parent = uuid4()
    kwargs["parent_span_id"] = parent
    msg = BaseMessage(**kwargs)
    assert msg.parent_span_id == parent
