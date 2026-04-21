import json
from pathlib import Path

import pytest


@pytest.fixture
def artifacts_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    d = tmp_path / "artifacts"
    d.mkdir()
    monkeypatch.setenv("PEDAGOGICA_ARTIFACTS_DIR", str(d))
    return d


@pytest.fixture
def job_dir(artifacts_dir: Path) -> Path:
    d = artifacts_dir / "job-abc"
    d.mkdir()
    return d


@pytest.fixture
def job_id(job_dir: Path) -> str:
    return job_dir.name


@pytest.fixture
def minimal_job_state(job_dir: Path) -> dict:
    state = {
        "trace_id": "00000000-0000-0000-0000-000000000001",
        "span_id": "00000000-0000-0000-0000-000000000002",
        "parent_span_id": None,
        "timestamp": "2026-04-20T22:00:00+00:00",
        "producer": "orchestrator",
        "schema_version": "0.0.1",
        "job_id": "00000000-0000-0000-0000-000000000abc",
        "created_at": "2026-04-20T22:00:00+00:00",
        "user_prompt": "explain derivatives",
        "skills_pinned": {},
        "models_default": {},
        "stages": [
            {
                "name": "intake",
                "status": "complete",
                "started_at": "2026-04-20T22:00:00+00:00",
                "completed_at": "2026-04-20T22:00:03+00:00",
                "artifact_path": "01_intake.json",
                "cost_usd": 0.0,
                "token_counts": {},
            },
            {
                "name": "curriculum",
                "status": "in_progress",
                "started_at": "2026-04-20T22:00:03+00:00",
                "completed_at": None,
                "artifact_path": None,
                "cost_usd": 0.0,
                "token_counts": {},
            },
            {
                "name": "storyboard",
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "artifact_path": None,
                "cost_usd": 0.0,
                "token_counts": {},
            },
        ],
        "current_stage": "curriculum",
        "terminal": False,
        "final_artifact_paths": {},
    }
    (job_dir / "job_state.json").write_text(json.dumps(state))
    return state
