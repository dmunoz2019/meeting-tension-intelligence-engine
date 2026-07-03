from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from .models import AdaptivePattern, TranscriptUnit
from .rules import UNIVERSAL_SEEDS
from .text import tokenize

STOPWORDS = {
    "a", "al", "algo", "ante", "asi", "aunque", "cada", "como", "con", "cual", "cuando",
    "de", "del", "desde", "donde", "el", "ella", "en", "entre", "es", "esa", "ese", "eso",
    "esta", "este", "fue", "ha", "hacia", "la", "las", "le", "lo", "los", "mas", "me", "mi",
    "mucho", "muy", "nada", "ni", "nos", "o", "otra", "otro", "para", "por", "porque", "pues",
    "que", "quien", "se", "si", "sobre", "son", "su", "sus", "tambien", "todo", "tu", "un",
    "una", "uno", "y", "ya", "yo",
}


def seed_groups(text: str) -> list[str]:
    hits: list[str] = []
    for group, patterns in UNIVERSAL_SEEDS.items():
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
            hits.append(group)
    return hits


def ngrams(text: str, maximum: int = 5) -> set[str]:
    words = tokenize(text)
    output: set[str] = set()
    for size in range(1, min(maximum, len(words)) + 1):
        for index in range(len(words) - size + 1):
            gram_words = words[index:index + size]
            if all(word in STOPWORDS for word in gram_words):
                continue
            if size > 1 and (gram_words[0] in STOPWORDS or gram_words[-1] in STOPWORDS):
                continue
            output.add(" ".join(gram_words))
    return output


def phrase_python_regex(phrase: str) -> str:
    return r"\b" + r"\s+".join(re.escape(word) for word in phrase.split()) + r"\b"


def phrase_posix_ere(phrase: str) -> str:
    middle = "[[:space:]]+".join(re.escape(word) for word in phrase.split())
    return f"(^|[[:space:][:punct:]]){middle}([[:space:][:punct:]]|$)"


def discover_patterns(
    units: list[TranscriptUnit],
    limit: int = 80,
    minimum_score: float = 1.2,
) -> list[AdaptivePattern]:
    candidates = [unit for unit in units if seed_groups(unit.normalized)]
    background = [unit for unit in units if not seed_groups(unit.normalized)]
    candidate_df: Counter[str] = Counter()
    background_df: Counter[str] = Counter()
    examples: dict[str, list[str]] = defaultdict(list)

    for unit in candidates:
        grams = ngrams(unit.normalized)
        candidate_df.update(grams)
        for gram in grams:
            if len(examples[gram]) < 2:
                examples[gram].append(unit.text)

    for unit in background:
        background_df.update(ngrams(unit.normalized))

    scored: list[tuple[float, str, int, int, float]] = []
    candidate_count = max(1, len(candidates))
    background_count = max(1, len(background))
    generic = {"proceso", "sistema", "empresa", "informacion", "trabajo", "parte", "forma", "idea"}

    for phrase, support in candidate_df.items():
        background_support = background_df.get(phrase, 0)
        if support < 2 and len(phrase.split()) == 1:
            continue
        candidate_rate = (support + 0.5) / (candidate_count + 1.0)
        background_rate = (background_support + 0.5) / (background_count + 1.0)
        lift = candidate_rate / background_rate
        length_bonus = 1.0 + 0.18 * min(len(phrase.split()) - 1, 4)
        score = math.log1p(lift) * math.log1p(support) * length_bonus
        if phrase in generic:
            score *= 0.15
        if score >= minimum_score:
            scored.append((score, phrase, support, background_support, lift))

    scored.sort(reverse=True)
    selected: list[AdaptivePattern] = []
    for score, phrase, support, background_support, lift in scored:
        if any(
            phrase in existing.phrase and support == existing.support
            for existing in selected
        ):
            continue
        selected.append(
            AdaptivePattern(
                pattern_id=f"AUTO_{len(selected) + 1:03d}",
                phrase=phrase,
                python_regex=phrase_python_regex(phrase),
                posix_ere=phrase_posix_ere(phrase),
                support=support,
                background_support=background_support,
                lift=round(lift, 3),
                score=round(score, 3),
            )
        )
        if len(selected) >= limit:
            break
    return selected
