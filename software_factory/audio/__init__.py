"""Audio and Text-to-Speech (TTS) synthesis module."""

from .tts_service import (
    DEFAULT_TTS_SERVICE,
    CloudTextToSpeechService,
    clean_markdown_for_speech,
)

__all__ = [
    "DEFAULT_TTS_SERVICE",
    "CloudTextToSpeechService",
    "clean_markdown_for_speech",
]
