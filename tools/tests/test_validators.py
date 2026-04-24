from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from pedagogica_schemas.script import Script
from pedagogica_schemas.storyboard import SceneBeat, Storyboard
from pedagogica_schemas.validators import (
    validate_script,
    validate_script_cadence,
    validate_storyboard_depth,
)
from pedagogica_tools.cli import app
from typer.testing import CliRunner


runner = CliRunner()


def _base_message() -> dict:
    return {
        "trace_id": uuid4(),
        "span_id": uuid4(),
        "producer": "test",
    }


def _script(scene_id: str, text: str) -> Script:
    return Script(
        **_base_message(),
        scene_id=scene_id,
        text=text,
        words=text.split(),
        estimated_duration_seconds=1.0,
    )


def _beat(
    scene_id: str,
    *,
    beat_type: str = "hook",
    target_duration_seconds: float = 40.0,
    learning_objective_id: str | None = "lo_1",
) -> SceneBeat:
    return SceneBeat(
        scene_id=scene_id,
        beat_type=beat_type,
        target_duration_seconds=target_duration_seconds,
        learning_objective_id=learning_objective_id,
        visual_intent="show the idea",
        narration_intent="explain the idea",
    )


def _storyboard(*beats: SceneBeat) -> Storyboard:
    return Storyboard(
        **_base_message(),
        topic="test topic",
        total_duration_seconds=sum(beat.target_duration_seconds for beat in beats),
        scenes=list(beats),
        voice_id="voice_123",
    )


def _write_model(path: Path, model) -> None:
    path.write_text(model.model_dump_json(), encoding="utf-8")


def _sentence(word: str, count: int, end: str = ".") -> str:
    return " ".join([word] * count) + end


def test_word_budget_fail() -> None:
    text = " ".join(["word"] * 200)

    report = validate_script_cadence(_script("scene_01", text), 40.0, "hook")

    assert report.passed is False
    assert any(
        issue.rule == "word_budget"
        and issue.severity == "error"
        and issue.observed == 5.0
        and issue.threshold == 2.75
        for issue in report.issues
    )


def test_word_budget_pass() -> None:
    text = " ".join(["word"] * 100)

    report = validate_script_cadence(_script("scene_01", text), 40.0, "hook")

    assert report.passed is True
    assert all(issue.rule != "word_budget" for issue in report.issues)


def test_short_sentence_ratio_fail() -> None:
    text = " ".join(_sentence("word", 10) for _ in range(10))

    report = validate_script_cadence(_script("scene_01", text), 40.0, "hook")

    assert any(issue.rule == "short_sentence_ratio" for issue in report.issues)


def test_short_sentence_ratio_pass() -> None:
    text = " ".join(
        [
            *[_sentence("short", 4) for _ in range(4)],
            *[_sentence("long", 10) for _ in range(6)],
        ]
    )

    report = validate_script_cadence(_script("scene_01", text), 40.0, "hook")

    assert all(issue.rule != "short_sentence_ratio" for issue in report.issues)


def test_question_density_fail() -> None:
    text = " ".join(["word"] * 100)

    report = validate_script_cadence(_script("scene_01", text), 40.0, "hook")

    assert any(issue.rule == "question_density" for issue in report.issues)


def test_first_person_density_pass() -> None:
    sentences = [
        "We try this with our graph right now and we compare outcomes.",
        "Let's test one more case so we can see our pattern.",
        "We keep our focus here while we try another example.",
        "We check our result and we keep our reasoning clear.",
    ]
    text = " ".join(sentences)

    report = validate_script_cadence(_script("scene_01", text), 40.0, "recap")

    assert all(issue.rule != "first_person_density" for issue in report.issues)


def test_demo_action_words_fail_and_recap_is_exempt() -> None:
    text = "We test the graph and we compare the result with our estimate."

    hook_report = validate_script_cadence(_script("scene_01", text), 40.0, "hook")
    recap_report = validate_script_cadence(_script("scene_01", text), 40.0, "recap")

    assert any(issue.rule == "demo_action_words" for issue in hook_report.issues)
    assert all(issue.rule != "demo_action_words" for issue in recap_report.issues)


def test_validate_script_uses_storyboard_scene_match() -> None:
    script = _script("scene_01", "We watch this now. Ready? We try it here.")
    storyboard = _storyboard(_beat("scene_01", beat_type="hook", target_duration_seconds=40.0))

    report = validate_script(script, storyboard)

    assert report.scene_id == "scene_01"


def test_check_script_cli_handles_warn_only_and_strict(tmp_path: Path) -> None:
    storyboard = _storyboard(_beat("scene_01", beat_type="hook", target_duration_seconds=40.0))
    script = _script("scene_01", " ".join(["word"] * 100))
    script_path = tmp_path / "script.json"
    storyboard_path = tmp_path / "storyboard.json"
    _write_model(script_path, script)
    _write_model(storyboard_path, storyboard)

    non_strict = runner.invoke(
        app, ["check-script", str(script_path), str(storyboard_path)]
    )
    strict = runner.invoke(
        app, ["check-script", str(script_path), str(storyboard_path), "--strict"]
    )

    assert non_strict.exit_code == 0, non_strict.stderr
    assert "question_density" in non_strict.stdout
    assert strict.exit_code == 1


def test_check_script_cli_exits_1_on_word_budget(tmp_path: Path) -> None:
    storyboard = _storyboard(_beat("scene_01", beat_type="hook", target_duration_seconds=40.0))
    script = _script("scene_01", " ".join(["word"] * 200))
    script_path = tmp_path / "script.json"
    storyboard_path = tmp_path / "storyboard.json"
    _write_model(script_path, script)
    _write_model(storyboard_path, storyboard)

    result = runner.invoke(app, ["check-script", str(script_path), str(storyboard_path)])

    assert result.exit_code == 1
    assert "word_budget" in result.stdout


def test_storyboard_depth_passes_for_180s_with_one_in_depth_lo() -> None:
    storyboard = _storyboard(
        _beat("scene_01", beat_type="define", target_duration_seconds=90.0),
        _beat("scene_02", beat_type="example", target_duration_seconds=90.0),
    )

    report = validate_storyboard_depth(storyboard)

    assert report.passed is True
    assert report.lo_count_in_depth == 1
    assert all(issue.rule != "lo_cap" for issue in report.issues)


def test_storyboard_depth_fails_for_180s_with_two_in_depth_los() -> None:
    storyboard = _storyboard(
        _beat(
            "scene_01",
            beat_type="define",
            target_duration_seconds=45.0,
            learning_objective_id="lo_1",
        ),
        _beat(
            "scene_02",
            beat_type="example",
            target_duration_seconds=45.0,
            learning_objective_id="lo_1",
        ),
        _beat(
            "scene_03",
            beat_type="define",
            target_duration_seconds=45.0,
            learning_objective_id="lo_2",
        ),
        _beat(
            "scene_04",
            beat_type="example",
            target_duration_seconds=45.0,
            learning_objective_id="lo_2",
        ),
    )

    report = validate_storyboard_depth(storyboard)

    assert report.passed is False
    assert report.lo_count_in_depth == 2
    assert any(
        issue.rule == "lo_cap"
        and issue.severity == "error"
        and issue.observed == 2
        and issue.threshold == 1
        for issue in report.issues
    )


def test_storyboard_depth_passes_for_300s_with_two_in_depth_los() -> None:
    storyboard = _storyboard(
        _beat(
            "scene_01",
            beat_type="define",
            target_duration_seconds=75.0,
            learning_objective_id="lo_1",
        ),
        _beat(
            "scene_02",
            beat_type="example",
            target_duration_seconds=75.0,
            learning_objective_id="lo_1",
        ),
        _beat(
            "scene_03",
            beat_type="define",
            target_duration_seconds=75.0,
            learning_objective_id="lo_2",
        ),
        _beat(
            "scene_04",
            beat_type="example",
            target_duration_seconds=75.0,
            learning_objective_id="lo_2",
        ),
    )

    report = validate_storyboard_depth(storyboard)

    assert report.passed is True
    assert report.lo_count_in_depth == 2
    assert all(issue.rule != "lo_cap" for issue in report.issues)


def test_storyboard_depth_warns_on_hook_with_learning_objective() -> None:
    storyboard = _storyboard(
        _beat(
            "scene_01",
            beat_type="hook",
            target_duration_seconds=90.0,
            learning_objective_id="lo_1",
        ),
        _beat(
            "scene_02",
            beat_type="define",
            target_duration_seconds=90.0,
            learning_objective_id="lo_1",
        ),
    )

    report = validate_storyboard_depth(storyboard)

    assert any(issue.rule == "hook_recap_no_lo" for issue in report.issues)


def test_storyboard_depth_warns_when_example_precedes_define() -> None:
    storyboard = _storyboard(
        _beat(
            "scene_01",
            beat_type="example",
            target_duration_seconds=90.0,
            learning_objective_id="lo_1",
        ),
        _beat(
            "scene_02",
            beat_type="define",
            target_duration_seconds=90.0,
            learning_objective_id="lo_1",
        ),
    )

    report = validate_storyboard_depth(storyboard)

    assert any(issue.rule == "define_has_example" for issue in report.issues)


def test_check_storyboard_cli_handles_warn_only_and_strict(tmp_path: Path) -> None:
    storyboard = _storyboard(
        _beat(
            "scene_01",
            beat_type="hook",
            target_duration_seconds=90.0,
            learning_objective_id="lo_1",
        ),
        _beat(
            "scene_02",
            beat_type="define",
            target_duration_seconds=90.0,
            learning_objective_id="lo_1",
        ),
    )
    storyboard_path = tmp_path / "storyboard.json"
    _write_model(storyboard_path, storyboard)

    non_strict = runner.invoke(app, ["check-storyboard", str(storyboard_path)])
    strict = runner.invoke(app, ["check-storyboard", str(storyboard_path), "--strict"])

    assert non_strict.exit_code == 0, non_strict.stderr
    assert "hook_recap_no_lo" in non_strict.stdout
    assert strict.exit_code == 1
