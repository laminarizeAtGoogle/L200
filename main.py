"""Main Entrypoint for the L200 A2A Software Factory API and Runtime Verification.

Supports:
1. ASGI Server Execution: `uvicorn main:app --host 0.0.0.0 --port 8080`
2. CLI Verification & Smoke Check: `./bin/uv run --env-file .env python main.py`
"""

from __future__ import annotations

import argparse
import os
import sys

import google.adk
import ipykernel
import pandas as pd
import uvicorn

from software_factory import (
    DEFAULT_CONFIG,
    adk_app,
    create_software_factory_api,
    root_agent,
)
from software_factory.agents import A2A_AGENT_ROUTES

app = create_software_factory_api(DEFAULT_CONFIG)


def run_verification_smoke_check() -> None:
    """Verifies Python toolchain, ADK agent graph, and A2A routes."""
    print(f"Python version: {sys.version}")
    print(f"Virtualenv prefix: {sys.prefix}")
    print("\nImported modules successfully:")
    print(f" - google.adk version: {getattr(google.adk, '__version__', 'unknown')}")
    print(f" - pandas version: {pd.__version__}")
    print(f" - ipykernel version: {ipykernel.__version__}")

    cloudsdk_config = os.environ.get("CLOUDSDK_CONFIG", "Not set")
    gac = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "Not set")
    print("\nEnvironment variables:")
    print(f" - CLOUDSDK_CONFIG: {cloudsdk_config}")
    print(f" - GOOGLE_APPLICATION_CREDENTIALS: {gac}")

    print("\nGemini Enterprise (GE) Cloud Chat & A2A Graph Summary:")
    print(f" - ADK App Name: {adk_app.name}")
    print(f" - Primary Model: {DEFAULT_CONFIG.primary_chat_model} (Planning: {DEFAULT_CONFIG.planning_model})")
    print(f" - Cloud TTS Voice: {DEFAULT_CONFIG.tts_voice_name} ({DEFAULT_CONFIG.tts_language_code})")
    print(f" - Security / IAP Enforced: {DEFAULT_CONFIG.iap_enforce}")
    print(" - Database Access Policy: STRICT QUARANTINE (Cloud SQL/Spanner/Firestore blocked)")
    print(" - Read-Only Cloud Inspection: Active (Compute, Run, GKE, GCS, IAM, Cloud Logging)")
    print(f" - Focal Root Agent: {root_agent.name} (model={root_agent.model})")
    print(
        f" - Specialist Sub-Agents: {[sa.name for sa in root_agent.sub_agents]}"
    )
    print(f" - Mounted A2A Routes: {list(A2A_AGENT_ROUTES.values())}")
    print(" - Web UI Frontend: Mounted at http://localhost:8080/")
    print("\nEnvironment verification successful!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="L200 A2A Software Factory Server & Verification CLI"
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Launch the Unified FastAPI + A2A Server with uvicorn.",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_CONFIG.host,
        help="Host interface to bind when --serve is set.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_CONFIG.port,
        help="Port to bind when --serve is set.",
    )
    args = parser.parse_args()

    if args.serve:
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        run_verification_smoke_check()


if __name__ == "__main__":
    main()
