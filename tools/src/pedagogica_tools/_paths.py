import os
from pathlib import Path


def artifacts_root() -> Path:
    override = os.environ.get("PEDAGOGICA_ARTIFACTS_DIR")
    if override:
        return Path(override).resolve()
    return (Path.cwd() / "artifacts").resolve()


def job_dir(job_id: str) -> Path:
    return artifacts_root() / job_id


def trace_path(job_id: str) -> Path:
    return job_dir(job_id) / "trace.jsonl"


def job_state_path(job_id: str) -> Path:
    return job_dir(job_id) / "job_state.json"
