"""Optional upstream adapters.

All adapters use lazy imports so the core package remains lightweight.
"""

from .faster_whisper import FasterWhisperASR
from .presidio import PresidioPIIRedactor
from .pyannote import PyannoteDiarizer

__all__ = ["FasterWhisperASR", "PresidioPIIRedactor", "PyannoteDiarizer"]
