import json
from pathlib import Path

import pytest
from pedagogica_tools._trace import append_event
from pedagogica_tools._view import render_timeline


def test_render_timeline_errors_without_job_state(job_id: str) -> None:
    with pytest.raises(FileNotFoundError, match="job_state.json"):
        render_timeline(job_id)


def test_render_timeline_shows_header_fields(job_id: str, minimal_job_state: dict) -> None:
    out = render_timeline(job_id)
    assert minimal_job_state["job_id"] in out
    assert minimal_job_state["created_at"] in out
    assert "explain derivatives" in out
    assert "terminal" in out
    assert "curriculum" in out


def test_render_timeline_lists_each_stage_row(job_id: str, minimal_job_state: dict) -> None:
    out = render_timeline(job_id)
    for stage in minimal_job_state["stages"]:
        assert stage["name"] in out
        assert stage["status"] in out


def test_render_timeline_formats_completed_stage_duration(
    job_id: str, minimal_job_state: dict
) -> None:
    out = render_timeline(job_id)
    # intake ran 22:00:00 -> 22:00:03 = 3.0s
    assert "3.0s" in out


def test_render_timeline_dashes_when_stage_has_no_duration(
    job_id: str, minimal_job_state: dict
) -> None:
    # curriculum is in_progress (no completed_at), storyboard is pending
    out = render_timeline(job_id)
    # at least one em-dash should appear in the duration column
    assert "—" in out


def test_render_timeline_aggregates_event_costs(
    job_id: str, minimal_job_state: dict
) -> None:
    append_event(
        job_id,
        json.dumps(
            {
                "event": "llm_call",
                "input_tokens": 1200,
                "output_tokens": 300,
                "cache_read_tokens": 800,
                "cost_usd": 0.0123,
            }
        ),
    )
    append_event(
        job_id,
        json.dumps(
            {
                "event": "tts_call",
                "cost_usd": 0.05,
            }
        ),
    )

    out = render_timeline(job_id)
    assert "input=1,200" in out
    assert "output=300" in out
    assert "cache_read=800" in out
    assert "$0.0623" in out
    assert "events       2" in out


def test_render_timeline_handles_zero_events(
    job_id: str, minimal_job_state: dict
) -> None:
    out = render_timeline(job_id)
    assert "events       0" in out
    assert "$0.0000" in out


def test_render_timeline_respects_artifacts_override(
    artifacts_dir: Path, minimal_job_state: dict, job_id: str
) -> None:
    # minimal_job_state wrote under $PEDAGOGICA_ARTIFACTS_DIR/job-abc — prove we
    # read it from there, not from cwd/artifacts.
    out = render_timeline(job_id)
    assert "explain derivatives" in out
