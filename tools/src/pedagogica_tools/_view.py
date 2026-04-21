import json
from datetime import datetime
from typing import Iterable

from pedagogica_tools._paths import job_state_path
from pedagogica_tools._trace import read_events


def _parse_ts(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m{secs:02d}s"


def _stage_duration(stage: dict) -> float | None:
    start = _parse_ts(stage.get("started_at") or "")
    end = _parse_ts(stage.get("completed_at") or "")
    if start and end:
        return (end - start).total_seconds()
    return None


def _cost_line(events: Iterable[dict]) -> tuple[int, int, int, float]:
    in_tok = out_tok = cache_tok = 0
    cost = 0.0
    for e in events:
        in_tok += int(e.get("input_tokens") or 0)
        out_tok += int(e.get("output_tokens") or 0)
        cache_tok += int(e.get("cache_read_tokens") or 0)
        cost += float(e.get("cost_usd") or 0.0)
    return in_tok, out_tok, cache_tok, cost


def render_timeline(job_id: str) -> str:
    jsp = job_state_path(job_id)
    if not jsp.is_file():
        raise FileNotFoundError(f"job_state.json not found at {jsp}")

    state = json.loads(jsp.read_text(encoding="utf-8"))
    events = read_events(job_id)

    lines: list[str] = []
    lines.append(f"job_id       {state.get('job_id', job_id)}")
    lines.append(f"created_at   {state.get('created_at', '—')}")
    lines.append(f"prompt       {state.get('user_prompt', '')}")
    lines.append(f"terminal     {state.get('terminal', False)}")
    lines.append(f"current      {state.get('current_stage') or '—'}")
    lines.append("")
    lines.append(f"{'stage':<16} {'status':<12} {'duration':>10}  artifact")
    lines.append("-" * 64)
    for stage in state.get("stages", []):
        lines.append(
            f"{stage.get('name', ''):<16} "
            f"{stage.get('status', ''):<12} "
            f"{_fmt_duration(_stage_duration(stage)):>10}  "
            f"{stage.get('artifact_path') or ''}"
        )
    lines.append("")

    in_tok, out_tok, cache_tok, cost = _cost_line(events)
    lines.append(
        f"tokens       input={in_tok:,}  output={out_tok:,}  cache_read={cache_tok:,}"
    )
    lines.append(f"cost_usd     ${cost:.4f}  (ElevenLabs + any billable LLM)")
    lines.append(f"events       {len(events)}")

    return "\n".join(lines) + "\n"
