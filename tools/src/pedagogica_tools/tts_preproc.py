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
    # Names
    PronunciationRule(r"\bBernoulli\b", "Bernooli", "Bernoulli phonetic"),
    PronunciationRule(r"\bEuler\b", "Oyler", "Euler phonetic"),
    PronunciationRule(r"\bLagrange\b", "La-grahnj", "Lagrange phonetic"),
    PronunciationRule(r"\bCauchy\b", "Ko-shee", "Cauchy phonetic"),
    PronunciationRule(r"\bLaplace\b", "La-plahss", "Laplace phonetic"),
    PronunciationRule(r"\bGauss\b", "gowss", "Gauss phonetic"),
    PronunciationRule(r"\bFourier\b", "For-yay", "Fourier phonetic"),
    PronunciationRule(r"\bPoisson\b", "Pwah-sohn", "Poisson phonetic"),
    PronunciationRule(r"\bNewtonian\b", "Nyoo-toh-nee-an", "Newtonian phonetic"),
    # Greek letters
    PronunciationRule(r"\brho\b", "roe", "rho Greek letter"),
    PronunciationRule(r"\btheta\b", "thay-ta", "theta Greek letter"),
    PronunciationRule(r"\bphi\b", "fye", "phi Greek letter"),
    PronunciationRule(r"\bpsi\b", "sigh", "psi Greek letter"),
    PronunciationRule(r"\bmu\b", "myoo", "mu Greek letter"),
    PronunciationRule(r"\bnu\b", "noo", "nu Greek letter"),
    PronunciationRule(r"\bxi\b", "ksigh", "xi Greek letter"),
    PronunciationRule(r"\bchi\b", "kigh", "chi Greek letter"),
    PronunciationRule(r"\beta\b", "ay-ta", "eta Greek letter"),
    # Physics-specific common misreads
    PronunciationRule(r"\bincompressible\b", "incompressable", "common misread"),
    PronunciationRule(r"\beigenvalue\b", "eye-gen-value", "eigenvalue compound"),
    PronunciationRule(r"\beigenvector\b", "eye-gen-vector", "eigenvector compound"),
    # Math symbols / operators
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
