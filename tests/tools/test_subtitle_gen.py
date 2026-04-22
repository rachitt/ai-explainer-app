from pedagogica_schemas.audio import WordTiming
from pedagogica_tools.subtitle_gen import format_srt_time, format_vtt_time, group_word_timings


def _word(text: str, start: float, end: float) -> WordTiming:
    return WordTiming(
        word=text,
        start_seconds=start,
        end_seconds=end,
        char_start=0,
        char_end=len(text),
    )


def test_format_vtt_time() -> None:
    assert format_vtt_time(0.0) == "00:00:00.000"
    assert format_vtt_time(0.234) == "00:00:00.234"
    assert format_vtt_time(3600.0) == "01:00:00.000"
    assert format_vtt_time(3661.234) == "01:01:01.234"


def test_format_srt_time() -> None:
    assert format_srt_time(0.0) == "00:00:00,000"
    assert format_srt_time(0.234) == "00:00:00,234"
    assert format_srt_time(3600.0) == "01:00:00,000"
    assert format_srt_time(3661.234) == "01:01:01,234"


def test_group_word_timings_respects_character_budget() -> None:
    cues = group_word_timings(
        [
            _word("alpha", 0.0, 0.4),
            _word("beta", 0.5, 0.9),
            _word("gamma", 1.0, 1.4),
        ],
        max_chars_per_line=10,
        max_lines_per_cue=1,
        min_cue_seconds=0.0,
        max_cue_seconds=10.0,
    )

    assert [cue.text for cue in cues] == ["alpha beta", "gamma"]


def test_group_word_timings_splits_after_sentence_punctuation() -> None:
    cues = group_word_timings(
        [
            _word("Stop.", 0.0, 0.5),
            _word("Next", 0.7, 1.0),
            _word("idea", 1.1, 1.6),
        ],
        max_chars_per_line=42,
        max_lines_per_cue=2,
        min_cue_seconds=0.0,
        max_cue_seconds=10.0,
    )

    assert [cue.text for cue in cues] == ["Stop.", "Next idea"]


def test_group_word_timings_respects_max_cue_seconds() -> None:
    cues = group_word_timings(
        [
            _word("one", 0.0, 0.4),
            _word("two", 0.5, 1.0),
            _word("three", 1.1, 1.8),
        ],
        max_chars_per_line=42,
        max_lines_per_cue=2,
        min_cue_seconds=0.0,
        max_cue_seconds=1.2,
    )

    assert [cue.text for cue in cues] == ["one two", "three"]
