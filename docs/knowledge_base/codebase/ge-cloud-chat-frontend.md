---
okf_version: "1.0"
entry_id: "ge-cloud-chat-frontend"
entry_name: "Gemini Enterprise Web Frontend"
category: "codebase"
sub_category: "user_interface"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Gemini Enterprise & UI Engineering / Academy L200"
dendrite_node_id: "ge_frontend"
discovered_by: "static_analysis"
last_verified: "2026-09-29"
---

# OKF (Codebase): Gemini Enterprise Web Frontend

## 1. Executive Summary & Purpose
- **Primary Function**: Delivers a rich, multimodal conversational interface modeled after Google Gemini Enterprise and Google Cloud Console, supporting text input, real-time voice speech recognition (Web Speech API), and audio synthesis (Cloud TTS playback).
- **Target Audience / Consumer**: Cloud developers, system administrators, and site reliability engineers chatting with their Google Cloud infrastructure.
- **Key Outcome**: Enables voice- and text-driven cloud observability, resource querying, and diagnostics with Identity-Aware Proxy (IAP) verified user identity.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `Zone1_Perimeter` (Client ingress and presentation).
- **Inbound Connections**: User browser interactions (text keystrokes, microphone speech capture).
- **Outbound Connections**: `iap_gateway` / `cloud_chat_agent` via `POST /api/v1/chat`, `POST /api/v1/tts`, and `GET /api/v1/me`.
- **Trust Boundary & Security Classification**: Protected by Google Cloud Identity-Aware Proxy (IAP); zero client-side privilege; direct database access is blocked at the backend.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - HTML & CSS & JS: [`software_factory/frontend/index.html`](../../../software_factory/frontend/index.html)
  - Backend route: [`software_factory/api/server.py`](../../../software_factory/api/server.py) (`GET /`)
- **Protocols & Interfaces**: HTTP/2, HTTPS, Web Speech Recognition (`webkitSpeechRecognition`), HTML5 Web Audio (`AudioContext`), Base64 MP3 audio decoding.
- **Features**:
  - Live Gemini 3.8 Flash model status badge
  - IAP user email chip and verified avatar
  - Microphone voice recording button with pulsing ripple animations
  - Audio waveform player with auto-play toggle
  - Quick action prompt chips for Compute, Cloud Run, GCS, IAM, and Cloud Logging
  - Collapsible IAP identity simulation bar for testing authorization tiers

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**: Served directly by the containerized FastAPI server at root (`http://localhost:8080/`).
- **Verification & Health Checks**:
  ```bash
  curl -s http://localhost:8080/ | grep "Gemini Enterprise"
  ./bin/uv run pytest tests/test_ge_cloud_chat_suite.py -k test_gemini_enterprise_frontend_served
  ```
- **Troubleshooting**: Inspect browser developer console for Web Speech API microphone permissions and audio playback autoplay policies.

## 5. References & Linked Assets
- Parent specification: [`AI in 5 Days Assessment Agent.md`](../../../AI%20in%205%20Days%20Assessment%20Agent.md)
- Backend API server: [`docs/knowledge_base/codebase/a2a-software-factory-api.md`](a2a-software-factory-api.md)
- Dendrite diagram: [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
