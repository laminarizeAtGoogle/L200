"""Google Cloud Text-to-Speech (TTS) integration service.

Provides high-fidelity neural voice synthesis for the Gemini Enterprise
Cloud Chat frontend:
1. Normalizes and cleans conversational markdown into speech-friendly prose.
2. Calls `google.cloud.texttospeech` with Journey/Neural2 voice presets.
3. Provides fallback audio synthesis when running in offline or mock test suites.
4. Returns Base64-encoded audio for direct browser streaming and playback.
"""

from __future__ import annotations

import base64
import io
import re
import struct
import wave
from typing import Any

from ..config import DEFAULT_CONFIG, FactoryConfig
from ..observability import DEFAULT_LOGGER, DEFAULT_TELEMETRY
from ..schemas import TtsSynthesisRequest, TtsSynthesisResponse


def clean_markdown_for_speech(text: str) -> str:
    """Converts markdown formatting, tables, and code snippets into smooth spoken prose."""
    if not text:
        return ""

    # Replace markdown headers
    cleaned = re.sub(r"#+\s*(.*)", r"\1.", text)

    # Remove code blocks entirely or replace with descriptive phrase
    cleaned = re.sub(r"```[\w]*\n(.*?)```", r"Code snippet omitted.", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)

    # Replace bullet points with brief pauses
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)

    # Replace markdown bold and italics
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)

    # Remove markdown links, keep text: [text](url) -> text
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)

    # Replace markdown tables with summary text
    cleaned = re.sub(
        r"(?:^\s*\|[^\n]+\|\s*\n?)+",
        "Table details summarized in text. ",
        cleaned,
        flags=re.MULTILINE,
    )

    # Collapse multiple whitespaces and clean newlines
    cleaned = re.sub(r"\n+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Limit speech length to first 1200 characters for snappy voice response
    if len(cleaned) > 1200:
        cleaned = cleaned[:1197] + "..."

    return cleaned


def _generate_fallback_wav_bytes(duration_ms: int = 500) -> bytes:
    """Generates a minimal valid PCM WAV audio byte buffer as a graceful fallback."""
    sample_rate = 16000
    num_samples = int(sample_rate * (duration_ms / 1000.0))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        # Generate silence / very soft tone
        samples = [0] * num_samples
        packed = struct.pack(f"<{len(samples)}h", *samples)
        wav_file.writeframes(packed)
    return buffer.getvalue()


class CloudTextToSpeechService:
    """Enterprise Text-to-Speech client using Google Cloud Text-to-Speech API."""

    def __init__(self, config: FactoryConfig = DEFAULT_CONFIG) -> None:
        self.config = config
        self._client: Any = None
        self._init_attempted = False

    def _get_client(self) -> Any:
        """Lazily initializes the google.cloud.texttospeech client."""
        if not self._init_attempted:
            self._init_attempted = True
            try:
                from google.cloud import texttospeech
                self._client = texttospeech.TextToSpeechClient()
            except Exception as e:
                DEFAULT_LOGGER.log_event(
                    event_type="TTS_CLIENT_FALLBACK",
                    message="Cloud TTS client initialization fell back to mock/synthetic generator",
                    metadata={"reason": str(e)},
                )
                self._client = None
        return self._client

    async def synthesize(
        self,
        request: TtsSynthesisRequest,
    ) -> TtsSynthesisResponse:
        """Synthesizes text into high-fidelity voice audio."""
        with DEFAULT_TELEMETRY.start_span(
            "audio.synthesize_speech",
            attributes={
                "voice_name": request.voice_name or self.config.tts_voice_name,
                "language_code": request.language_code,
            },
        ):
            speech_text = clean_markdown_for_speech(request.text)
            voice_name = request.voice_name or self.config.tts_voice_name
            language_code = request.language_code or self.config.tts_language_code
            speaking_rate = request.speaking_rate or self.config.tts_speaking_rate

            client = self._get_client()
            if client is not None:
                try:
                    from google.cloud import texttospeech

                    synthesis_input = texttospeech.SynthesisInput(text=speech_text)
                    voice = texttospeech.VoiceSelectionParams(
                        language_code=language_code,
                        name=voice_name,
                    )
                    audio_config = texttospeech.AudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.MP3,
                        speaking_rate=speaking_rate,
                    )

                    response = client.synthesize_speech(
                        input=synthesis_input,
                        voice=voice,
                        audio_config=audio_config,
                    )
                    audio_bytes = response.audio_content
                    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                    duration_est = max(0.5, len(speech_text.split()) / (2.5 * speaking_rate))

                    DEFAULT_LOGGER.log_event(
                        event_type="TTS_SYNTHESIS_SUCCESS",
                        message="Synthesized speech with Google Cloud Text-to-Speech API",
                        metadata={
                            "voice": voice_name,
                            "audio_bytes_length": len(audio_bytes),
                            "estimated_duration_s": duration_est,
                        },
                    )

                    return TtsSynthesisResponse(
                        audio_base64=audio_b64,
                        audio_content_type="audio/mp3",
                        duration_seconds=round(duration_est, 2),
                        voice_used=voice_name,
                    )
                except Exception as e:
                    DEFAULT_LOGGER.log_event(
                        event_type="TTS_API_CALL_FAILED",
                        message="Call to Cloud TTS API failed, generating fallback audio",
                        metadata={"error": str(e)},
                    )

            # Fallback audio generation
            wav_bytes = _generate_fallback_wav_bytes(duration_ms=600)
            audio_b64 = base64.b64encode(wav_bytes).decode("utf-8")
            return TtsSynthesisResponse(
                audio_base64=audio_b64,
                audio_content_type="audio/wav",
                duration_seconds=0.6,
                voice_used=f"{voice_name} (synthetic-fallback)",
            )


DEFAULT_TTS_SERVICE = CloudTextToSpeechService(DEFAULT_CONFIG)
