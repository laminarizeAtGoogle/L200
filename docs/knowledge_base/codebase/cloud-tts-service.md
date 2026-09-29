---
okf_version: "1.0"
entry_id: "cloud-tts-service"
entry_name: "Google Cloud Text-to-Speech (TTS) Voice Engine"
category: "codebase"
sub_category: "audio_and_speech"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Audio & Speech AI / Academy L200"
dendrite_node_id: "cloud_tts_engine"
discovered_by: "static_analysis"
last_verified: "2026-09-29"
---

# OKF (Codebase): Google Cloud Text-to-Speech (TTS) Voice Engine

## 1. Executive Summary & Purpose
- **Primary Function**: Converts agent conversational answers into natural, high-fidelity neural speech audio (Journey and Neural2 voice profiles) for streaming and playback in the Gemini Enterprise web frontend.
- **Target Audience / Consumer**: Users interacting with the Gemini Enterprise Cloud Chat interface via voice or listening to audio responses.
- **Key Outcome**: Enables hands-free, multimodal conversation with the cloud environment; includes automatic markdown cleaning to ensure spoken text is smooth, polite, and free of syntax tags or table formatting.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `Zone2_AgentEngine` voice synthesis provider.
- **Inbound Connections**: Invoked by `cloud_chat_agent` after conversational turn completion or via `POST /api/v1/tts`.
- **Outbound Connections**: Calls `texttospeech.googleapis.com` (gRPC / REST) to generate MP3/WAV audio bytes.
- **Trust Boundary & Security Classification**: Uses application default credentials or runtime service account (`a2a-software-factory-sa`); includes local fallback synthesizer when running offline.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - TTS Service: [`software_factory/audio/tts_service.py`](../../../software_factory/audio/tts_service.py)
  - Audio package exports: [`software_factory/audio/__init__.py`](../../../software_factory/audio/__init__.py)
  - Schemas: [`TtsSynthesisRequest`, `TtsSynthesisResponse` in `software_factory/schemas/models.py`](../../../software_factory/schemas/models.py)
- **Protocols & Interfaces**: Google Cloud Text-to-Speech Client (`google.cloud.texttospeech.TextToSpeechClient`), MP3 audio encoding, Base64 transmission.
- **Configuration & Environment Variables**:
  - `FACTORY_TTS_VOICE` (default: `en-US-Journey-F`)
  - `FACTORY_TTS_LANGUAGE` (default: `en-US`)
  - `FACTORY_TTS_SPEAKING_RATE` (default: `1.05`)

## 4. Operational Runbook & Lifecycle
- **Usage**:
  ```python
  from software_factory.audio import DEFAULT_TTS_SERVICE
  response = await DEFAULT_TTS_SERVICE.synthesize(
      TtsSynthesisRequest(text="Compute instance is active.", voice_name="en-US-Journey-F")
  )
  ```
- **Verification & Health Checks**:
  ```bash
  ./bin/uv run pytest tests/test_ge_cloud_chat_suite.py -k "test_tts"
  ```
- **Failure Modes & Blast Radius**:
  - Network timeouts or credential errors fall back seamlessly to generated PCM audio containers so unit tests and frontend audio players never crash.

## 5. References & Linked Assets
- Google Cloud Text-to-Speech: [https://cloud.google.com/text-to-speech/docs](https://cloud.google.com/text-to-speech/docs)
- Frontend client: [`docs/knowledge_base/codebase/ge-cloud-chat-frontend.md`](ge-cloud-chat-frontend.md)
- Dendrite model: [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
