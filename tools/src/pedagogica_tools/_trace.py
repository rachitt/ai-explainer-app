import json
from datetime import UTC, datetime

from pedagogica_tools._paths import job_dir, trace_path

ALLOWED_EVENTS = frozenset(
    {
        "stage_enter",
        "stage_exit",
        "llm_call",
        "tool_call",
        "manim_render",
        "manim_repair",
        "tts_call",
        "cache_hit",
        "cache_miss",
        "sandbox_violation",
        "cost_cap_hit",
        "error",
    }
)


def append_event(job_id: str, event_json: str) -> dict:
    """Validate + append a single event line to the job's trace.jsonl.

    Injects `ts` if missing. Returns the dict that was written.
    """
    jd = job_dir(job_id)
    if not jd.is_dir():
        raise FileNotFoundError(f"job dir does not exist: {jd}")

    try:
        event = json.loads(event_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"event is not valid JSON: {e}") from e

    if not isinstance(event, dict):
        raise ValueError("event must be a JSON object")

    name = event.get("event")
    if not name:
        raise ValueError("event is missing required field 'event'")
    if name not in ALLOWED_EVENTS:
        raise ValueError(
            f"unknown event type {name!r}; known: {sorted(ALLOWED_EVENTS)}"
        )

    event.setdefault("ts", datetime.now(UTC).isoformat())

    tp = trace_path(job_id)
    with tp.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, separators=(",", ":"), sort_keys=True) + "\n")

    return event


def read_events(job_id: str) -> list[dict]:
    tp = trace_path(job_id)
    if not tp.is_file():
        return []
    out: list[dict] = []
    for line in tp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out
