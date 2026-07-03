"""Optional upstream adapters.

All adapters use lazy imports so the core package remains lightweight.
"""

from .bge import BGEEmbeddingProvider, BGEReranker
from .faster_whisper import FasterWhisperASR
from .presidio import PresidioPIIRedactor
from .pyannote import PyannoteDiarizer

__all__ = [
    "BGEEmbeddingProvider",
    "BGEReranker",
    "FasterWhisperASR",
    "PresidioPIIRedactor",
    "PyannoteDiarizer",
]
