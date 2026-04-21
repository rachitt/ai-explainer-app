import json
from pathlib import Path

from pedagogica_tools.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_view_prints_timeline(job_id: str, minimal_job_state: dict) -> None:
    result = runner.invoke(app, ["view", job_id])
    assert result.exit_code == 0, result.stderr
    assert "explain derivatives" in result.stdout
    assert "intake" in result.stdout
    assert "curriculum" in result.stdout


def test_view_exits_2_when_job_missing(artifacts_dir: Path) -> None:
    result = runner.invoke(app, ["view", "no-such-job"])
    assert result.exit_code == 2
    assert "job_state.json" in result.stderr


def test_trace_appends_event_and_exits_0(job_dir: Path, job_id: str) -> None:
    payload = json.dumps({"event": "stage_enter", "agent": "intake"})
    result = runner.invoke(app, ["trace", job_id, payload])
    assert result.exit_code == 0, result.stderr

    line = (job_dir / "trace.jsonl").read_text().strip()
    entry = json.loads(line)
    assert entry["event"] == "stage_enter"
    assert entry["agent"] == "intake"
    assert "ts" in entry


def test_trace_exits_1_on_invalid_event(job_id: str) -> None:
    result = runner.invoke(app, ["trace", job_id, json.dumps({"event": "bogus"})])
    assert result.exit_code == 1
    assert "unknown event type" in result.stderr


def test_trace_exits_1_on_malformed_json(job_id: str) -> None:
    result = runner.invoke(app, ["trace", job_id, "{not json}"])
    assert result.exit_code == 1
    assert "valid JSON" in result.stderr


def test_trace_exits_2_when_job_dir_missing(artifacts_dir: Path) -> None:
    result = runner.invoke(
        app, ["trace", "no-such-job", json.dumps({"event": "stage_enter"})]
    )
    assert result.exit_code == 2
    assert "job dir" in result.stderr
