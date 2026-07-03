from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .rules import HEDGE_RE, HYPOTHETICAL_RE, INTENSIFIERS, NEGATIVE_LEXICON, POSITIVE_LEXICON
from .text import normalize, tokenize

NEGATORS = {"no", "nunca", "jamas", "tampoco", "sin"}


@dataclass(slots=True)
class SentimentResult:
    positive_raw: float
    negative_raw: float
    polarity: float
    dissatisfaction: float
    satisfaction: float
    hypothetical: bool
    hedged: bool
    direct_concern: bool
    reported_concern: bool


def analyze_sentiment(text: str) -> SentimentResult:
    normalized = normalize(text)
    words = tokenize(normalized)
    positive = 0.0
    negative = 0.0
    negation_until = -1
    multiplier = 1.0

    for index, word in enumerate(words):
        if word in NEGATORS:
            negation_until = index + 4
            continue
        if word in INTENSIFIERS:
            multiplier = max(multiplier, INTENSIFIERS[word])
            continue

        negated = index <= negation_until
        negative_weight = NEGATIVE_LEXICON.get(word, 0.0)
        positive_weight = POSITIVE_LEXICON.get(word, 0.0)

        if negative_weight:
            if negated:
                positive += 0.55 * negative_weight * multiplier
            else:
                negative += negative_weight * multiplier
        if positive_weight:
            if negated:
                negative += 0.70 * positive_weight * multiplier
            else:
                positive += positive_weight * multiplier
        multiplier = 1.0

    direct_concern = bool(re.search(r"\b(?:me|nos) preocupa\b", normalized))
    reported_concern = bool(
        re.search(r"\b(?:entiendo|comprendo|reconozco) (?:tu|su|la) preocupacion\b", normalized)
    )
    if direct_concern:
        negative += 3.5
    if reported_concern:
        negative += 0.7

    hypothetical = bool(HYPOTHETICAL_RE.search(normalized))
    hedged = bool(HEDGE_RE.search(normalized))
    if hypothetical:
        negative *= 0.62
        positive *= 0.82
    elif hedged:
        negative *= 0.82
        positive *= 0.90

    polarity = math.tanh((positive - negative) / 5.0)
    dissatisfaction = 100 / (1 + math.exp(-((negative - 0.35 * positive) - 2.2)))
    satisfaction = 100 / (1 + math.exp(-((positive - 0.35 * negative) - 2.2)))
    return SentimentResult(
        positive_raw=round(positive, 3),
        negative_raw=round(negative, 3),
        polarity=round(polarity, 4),
        dissatisfaction=round(dissatisfaction, 1),
        satisfaction=round(satisfaction, 1),
        hypothetical=hypothetical,
        hedged=hedged,
        direct_concern=direct_concern,
        reported_concern=reported_concern,
    )
