from __future__ import annotations

import re
import unicodedata

from .models import TranscriptUnit

TIMESTAMP_RE = re.compile(r"\((\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})\)\s*")
SPEAKER_RE = re.compile(r"^(?P<speaker>[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ .'-]{1,60}):\s+(?P<text>.+)$")


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.lower())
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = re.sub(r"[^a-z0-9\s¿?¡!.,;:%/_-]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalize(text))


def split_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+|\n{2,}", text.strip())
    output: list[str] = []
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        if len(piece) <= 550:
            output.append(piece)
            continue
        output.extend(
            section.strip()
            for section in re.split(
                r"(?=\b(?:pero|sin embargo|entonces|ahora|porque|o sea|por eso)\b)",
                piece,
                flags=re.IGNORECASE,
            )
            if section.strip()
        )
    return output


def parse_transcript(text: str) -> list[TranscriptUnit]:
    matches = list(TIMESTAMP_RE.finditer(text))
    blocks: list[tuple[int, str | None, str | None, str]] = []

    if matches:
        for index, timestamp_match in enumerate(matches):
            body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            blocks.append(
                (
                    index + 1,
                    timestamp_match.group(1),
                    timestamp_match.group(2),
                    text[timestamp_match.end():body_end],
                )
            )
    else:
        blocks.append((1, None, None, text))

    units: list[TranscriptUnit] = []
    unit_id = 0
    for block_id, start, end, body in blocks:
        for sentence in split_sentences(body):
            unit_id += 1
            speaker: str | None = None
            speaker_match = SPEAKER_RE.match(sentence)
            if speaker_match:
                speaker = speaker_match.group("speaker").strip()
                sentence = speaker_match.group("text").strip()
            units.append(
                TranscriptUnit(
                    unit_id=unit_id,
                    block_id=block_id,
                    start=start,
                    end=end,
                    text=sentence,
                    normalized=normalize(sentence),
                    speaker=speaker,
                )
            )
    return units
