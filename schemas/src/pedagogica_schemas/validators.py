from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from pedagogica_schemas.intake import IntakeResult
from pedagogica_schemas.script import Script
from pedagogica_schemas.storyboard import Storyboard

_WORD_RE = re.compile(r"\b\w[\w']*\b")
_FIRST_PERSON_RE = re.compile(r"\b(we|we'?ve|we'?re|let'?s|our|us)\b", re.IGNORECASE)
_DEMO_ACTION_RE = re.compile(
    r"\b(watch|notice|here|ready|boom|look|see|try|imagine)\b", re.IGNORECASE
)

# A "derived-quantity" claim — a numerical quantity that depends on other
# quantities already established in the narration. The common failure mode:
# narration asserts "three volts dropped" without ever mentioning the current
# that produces it. Every derived-quantity mention below must be supported by
# a plausible derivation cue earlier in the script (input values, Ohm's law,
# current, etc.).
_DERIVED_CLAIM_RE = re.compile(
    r"\b(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
    r"(?:volts?|amps?|amperes?|watts?|joules?|ohms?|newtons?|metres?|meters?|"
    r"seconds?|degrees?)\s+"
    r"(?:dropped|drop|gone|lost|spent|across|over|through|"
    r"remaining|left|of\s+drop)",
    re.IGNORECASE,
)
# A derivation cue — anything that signals the narration is actually doing
# the math rather than asserting an answer. Covers Ohm's-law style
# assertions ("current is", "I equals", "V/R", "times"), explicit mentions
# of the input quantity, and general phrases like "so" or "which means".
_DERIVATION_CUE_RE = re.compile(
    r"\b(?:"
    r"current|amp(?:ere)?s?|resistance|voltage|force|mass|acceleration|"
    r"times|divided by|per|over|"
    r"ohm's law|kirchhoff|newton's|"
    r"so that|so we get|which gives|which means|therefore|"
    r"equal[s]?|=|"
    r"i\s*=|v\s*=|f\s*=|a\s*="
    r")\b",
    re.IGNORECASE,
)
STOPWORDS = {
    "the",
    "a",
    "an",
    "why",
    "how",
    "what",
    "when",
    "where",
    "does",
    "do",
    "is",
    "are",
    "it",
    "of",
    "to",
    "from",
    "in",
    "on",
    "that",
    "this",
    "at",
    "for",
    "with",
}


@dataclass
class ScriptCadenceIssue:
    rule: str
    severity: Literal["error", "warn"]
    observed: float | int | str
    threshold: float | int | str
    message: str


@dataclass
class ScriptCadenceReport:
    scene_id: str
    issues: list[ScriptCadenceIssue] = field(default_factory=list)
    passed: bool = True
    quotas_met: int = 0


@dataclass
class DepthBudgetIssue:
    rule: str
    severity: Literal["error", "warn"]
    observed: int | float
    threshold: int | float
    message: str


@dataclass
class DepthBudgetReport:
    topic: str
    total_duration_seconds: float
    lo_count_in_depth: int
    issues: list[DepthBudgetIssue] = field(default_factory=list)
    passed: bool = True


@dataclass
class HookQuestionIssue:
    rule: str
    severity: Literal["error", "warn"]
    message: str


@dataclass
class HookQuestionReport:
    intake_hook_question: str
    storyboard_hook_question: str
    issues: list[HookQuestionIssue] = field(default_factory=list)
    passed: bool = True


def _tokenize_words(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _tokenize_sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"[.?!](?:\s|$)", text) if sentence.strip()]


def _salient_tokens(text: str) -> set[str]:
    normalized = re.sub(r"[^\w\s]", " ", text.lower())
    return {
        token
        for token in normalized.split()
        if len(token) >= 4 and token not in STOPWORDS
    }


def validate_script_cadence(
    script: Script, target_duration_seconds: float, beat_type: str
) -> ScriptCadenceReport:
    words = _tokenize_words(script.text)
    word_count = len(words)
    report = ScriptCadenceReport(scene_id=script.scene_id)

    words_per_second = round(word_count / target_duration_seconds, 2)
    if word_count / target_duration_seconds > 2.75:
        report.issues.append(
            ScriptCadenceIssue(
                rule="word_budget",
                severity="error",
                observed=words_per_second,
                threshold=2.75,
                message=f"Word rate {words_per_second:.2f} wps exceeds 2.75 ceiling — script will rush.",
            )
        )
        report.passed = False
    else:
        report.quotas_met += 1

    if word_count < 25:
        report.quotas_met += 1
    else:
        sentences = _tokenize_sentences(script.text)
        short_sentence_count = sum(
            1 for sentence in sentences if len(_tokenize_words(sentence)) <= 6
        )
        short_sentence_ratio = (
            short_sentence_count / len(sentences) if sentences else 0.0
        )
        short_sentence_ratio = round(short_sentence_ratio, 2)
        if short_sentence_ratio < 0.25:
            report.issues.append(
                ScriptCadenceIssue(
                    rule="short_sentence_ratio",
                    severity="warn",
                    observed=short_sentence_ratio,
                    threshold=0.25,
                    message=(
                        f"Short-sentence ratio {short_sentence_ratio:.2f} is below the 0.25 floor."
                    ),
                )
            )
        else:
            report.quotas_met += 1

    if beat_type == "recap":
        report.quotas_met += 1
    else:
        question_count = script.text.count("?")
        question_target = word_count / 40
        question_density = round(question_count / question_target, 2) if question_target else 0.0
        if question_count < question_target:
            report.issues.append(
                ScriptCadenceIssue(
                    rule="question_density",
                    severity="warn",
                    observed=question_density,
                    threshold=1.0,
                    message=(
                        f"Question density {question_density:.2f} is below the 1.00 target."
                    ),
                )
            )
        else:
            report.quotas_met += 1

    first_person_count = len(_FIRST_PERSON_RE.findall(script.text))
    first_person_threshold = round(8 * word_count / 100, 2)
    if first_person_count < first_person_threshold:
        report.issues.append(
            ScriptCadenceIssue(
                rule="first_person_density",
                severity="warn",
                observed=first_person_count,
                threshold=first_person_threshold,
                message="First-person markers are below the 8-per-100-words floor.",
            )
        )
    else:
        report.quotas_met += 1

    if beat_type == "recap":
        report.quotas_met += 1
    else:
        demo_action_count = len(_DEMO_ACTION_RE.findall(script.text))
        if demo_action_count < 2:
            report.issues.append(
                ScriptCadenceIssue(
                    rule="demo_action_words",
                    severity="warn",
                    observed=demo_action_count,
                    threshold=2,
                    message="Demo-action vocabulary is below the 2-word floor.",
                )
            )
        else:
            report.quotas_met += 1

    # Derivation-chain check. If the script asserts derived quantities
    # ("three volts dropped", "six more volts gone") without ever setting
    # up the inputs that derive them (current, resistance, Ohm's law),
    # flag as a hard error — the viewer has no way to connect the claim
    # to the circuit. This is a teaching-correctness gate, not cadence.
    unsupported_claims: list[str] = []
    for match in _DERIVED_CLAIM_RE.finditer(script.text):
        prefix = script.text[: match.start()]
        if not _DERIVATION_CUE_RE.search(prefix):
            unsupported_claims.append(match.group(0))
    if unsupported_claims:
        report.issues.append(
            ScriptCadenceIssue(
                rule="derivation_chain",
                severity="error",
                observed=len(unsupported_claims),
                threshold=0,
                message=(
                    "Narration asserts derived quantities without prior derivation: "
                    + ", ".join(f"{claim!r}" for claim in unsupported_claims)
                    + ". Establish the inputs (current, resistance, Ohm's law) "
                      "before stating the derived values."
                ),
            )
        )
        report.passed = False

    return report


def validate_script(script: Script, storyboard: Storyboard) -> ScriptCadenceReport:
    beat = next((scene for scene in storyboard.scenes if scene.scene_id == script.scene_id), None)
    if beat is None:
        raise ValueError(f"scene_id {script.scene_id!r} not found in storyboard scenes")
    return validate_script_cadence(
        script,
        beat.target_duration_seconds,
        beat.beat_type,
    )


def validate_storyboard_depth(storyboard: Storyboard) -> DepthBudgetReport:
    total_duration_seconds = sum(beat.target_duration_seconds for beat in storyboard.scenes)
    beats_by_lo: dict[str, dict[str, list[int]]] = {}
    report = DepthBudgetReport(
        topic=storyboard.topic,
        total_duration_seconds=total_duration_seconds,
        lo_count_in_depth=0,
    )

    for index, beat in enumerate(storyboard.scenes):
        if beat.learning_objective_id is None:
            continue
        lo_beats = beats_by_lo.setdefault(
            beat.learning_objective_id,
            {"define": [], "example": []},
        )
        if beat.beat_type in lo_beats:
            lo_beats[beat.beat_type].append(index)

    in_depth_los = {
        lo_id: beat_indices
        for lo_id, beat_indices in beats_by_lo.items()
        if beat_indices["define"] and beat_indices["example"]
    }
    report.lo_count_in_depth = len(in_depth_los)

    cap: int | None = None
    if 60 <= total_duration_seconds < 240:
        cap = 1
    elif 240 <= total_duration_seconds < 360:
        cap = 2
    elif 360 <= total_duration_seconds <= 600:
        cap = 3
    else:
        report.issues.append(
            DepthBudgetIssue(
                rule="duration_out_of_range",
                severity="warn",
                observed=total_duration_seconds,
                threshold=60,
                message="Storyboard duration is outside the 60s to 600s depth-budget range.",
            )
        )

    if cap is not None and report.lo_count_in_depth > cap:
        report.issues.append(
            DepthBudgetIssue(
                rule="lo_cap",
                severity="error",
                observed=report.lo_count_in_depth,
                threshold=cap,
                message=(
                    f"In-depth learning objectives {report.lo_count_in_depth} exceed the cap of {cap}."
                ),
            )
        )
        report.passed = False

    for lo_id, beat_indices in in_depth_los.items():
        if beat_indices["example"][0] < beat_indices["define"][0]:
            report.issues.append(
                DepthBudgetIssue(
                    rule="define_has_example",
                    severity="warn",
                    observed=beat_indices["example"][0],
                    threshold=beat_indices["define"][0],
                    message=(
                        f"Learning objective {lo_id} has its first example beat before its first define beat."
                    ),
                )
            )

    for beat in storyboard.scenes:
        if beat.beat_type in {"hook", "recap"} and beat.learning_objective_id is not None:
            report.issues.append(
                DepthBudgetIssue(
                    rule="hook_recap_no_lo",
                    severity="warn",
                    observed=1,
                    threshold=0,
                    message=(
                        f"{beat.beat_type} beat {beat.scene_id} should not set learning_objective_id."
                    ),
                )
            )

    return report


def validate_hook_question_propagation(
    intake: IntakeResult, storyboard: Storyboard
) -> HookQuestionReport:
    report = HookQuestionReport(
        intake_hook_question=intake.hook_question,
        storyboard_hook_question=storyboard.hook_question,
    )

    if storyboard.hook_question.strip() != intake.hook_question.strip():
        report.issues.append(
            HookQuestionIssue(
                rule="hook_question_mismatch",
                severity="error",
                message="storyboard.hook_question must match intake.hook_question exactly",
            )
        )

    first_scene = storyboard.scenes[0] if storyboard.scenes else None
    if first_scene is not None and first_scene.beat_type == "hook":
        narration = first_scene.narration_intent.lower()
        salient_tokens = _salient_tokens(intake.hook_question)
        if salient_tokens and not any(token in narration for token in salient_tokens):
            report.issues.append(
                HookQuestionIssue(
                    rule="hook_beat_not_anchored",
                    severity="warn",
                    message=(
                        "hook beat narration_intent should reuse at least one salient token "
                        "from the hook_question"
                    ),
                )
            )

    report.passed = not any(issue.severity == "error" for issue in report.issues)
    return report
