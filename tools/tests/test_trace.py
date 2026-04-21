import json
from pathlib import Path

import pytest
from pedagogica_tools._trace import append_event, read_events


def test_append_event_writes_jsonl_line(job_dir: Path, job_id: str) -> None:
    payload = json.dumps({"event": "stage_enter", "agent": "intake"})
    append_event(job_id, payload)

    trace_file = job_dir / "trace.jsonl"
    lines = trace_file.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["event"] == "stage_enter"
    assert entry["agent"] == "intake"
    assert "ts" in entry


def test_append_event_injects_ts_when_missing(job_id: str) -> None:
    event = append_event(job_id, json.dumps({"event": "cache_hit"}))
    assert event["ts"]


def test_append_event_keeps_explicit_ts(job_id: str) -> None:
    ts = "2026-01-01T00:00:00+00:00"
    event = append_event(job_id, json.dumps({"event": "cache_hit", "ts": ts}))
    assert event["ts"] == ts


def test_append_multiple_events_preserves_order(job_dir: Path, job_id: str) -> None:
    for name in ["stage_enter", "llm_call", "stage_exit"]:
        append_event(job_id, json.dumps({"event": name}))
    names = [e["event"] for e in read_events(job_id)]
    assert names == ["stage_enter", "llm_call", "stage_exit"]


def test_append_event_rejects_invalid_json(job_id: str) -> None:
    with pytest.raises(ValueError, match="not valid JSON"):
        append_event(job_id, "{not json}")


def test_append_event_rejects_non_object(job_id: str) -> None:
    with pytest.raises(ValueError, match="JSON object"):
        append_event(job_id, "[1,2,3]")


def test_append_event_rejects_missing_event_field(job_id: str) -> None:
    with pytest.raises(ValueError, match="'event'"):
        append_event(job_id, json.dumps({"agent": "intake"}))


def test_append_event_rejects_unknown_event_type(job_id: str) -> None:
    with pytest.raises(ValueError, match="unknown event type"):
        append_event(job_id, json.dumps({"event": "bogus_type"}))


def test_append_event_errors_on_missing_job_dir(artifacts_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        append_event("does-not-exist", json.dumps({"event": "stage_enter"}))


def test_read_events_returns_empty_for_new_job(job_id: str) -> None:
    assert read_events(job_id) == []
