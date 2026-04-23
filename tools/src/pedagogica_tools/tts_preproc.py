"""Pronunciation-hint preprocessing for text-to-speech input."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class PronunciationRule:
    pattern: str
    replacement: str
    reason: str


DEFAULT_RULES: tuple[PronunciationRule, ...] = (
    PronunciationRule(r"\bBernoulli\b", "Bernooli", "Bernoulli phonetic"),
    PronunciationRule(r"\brho\b", "roe", "rho Greek letter"),
    PronunciationRule(r"\bincompressible\b", "incompressable", "common misread"),
    PronunciationRule(r"\btheta\b", "thay-ta", "theta Greek letter"),
    PronunciationRule(r"\bEuler\b", "Oyler", "Euler phonetic"),
    PronunciationRule(r"\bLagrange\b", "La-grahnj", "Lagrange phonetic"),
    PronunciationRule(r"\bnabla\b", "nab-la", "nabla operator"),
)


def apply_rules(
    text: str,
    rules: Sequence[PronunciationRule] = DEFAULT_RULES,
) -> tuple[str, list[PronunciationRule]]:
    """Return text rewritten for TTS plus the rules that matched at least once."""
    rewritten = text
    fired: list[PronunciationRule] = []

    for rule in rules:
        if re.search(r"\s", rule.replacement):
            raise ValueError(
                f"pronunciation replacement must be a single token: {rule!r}"
            )

        rewritten, count = re.subn(
            rule.pattern,
            rule.replacement,
            rewritten,
            flags=re.IGNORECASE,
        )
        if count:
            fired.append(rule)

    return rewritten, fired
