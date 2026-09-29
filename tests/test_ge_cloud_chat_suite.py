"""Comprehensive verification suite for the Gemini Enterprise Cloud Chat Agent.

Tests:
1. IAP Verification & Zero-Trust Caller Authorization
2. Strict Database Access Restriction Guardrail (Zero direct DB queries, Logging allowed)
3. Dedicated Read-Only Cloud Infrastructure Probing (Compute, Run, GCS, IAM, Logging)
4. Cloud Text-to-Speech (TTS) Voice Engine and Markdown Speech Cleaner
5. Gemini Enterprise Frontend HTML & Endpoints
"""

from __future__ import annotations

import base64
from typing import Any
import pytest
from fastapi.testclient import TestClient

from software_factory.audio import DEFAULT_TTS_SERVICE, clean_markdown_for_speech
from software_factory.config import FactoryConfig
from software_factory.orchestration.database_guardrail import DatabaseAccessBlockerGuardrail
from software_factory.schemas import (
    CloudChatRequest,
    CloudChatResponse,
    IapUserIdentity,
    QueryCloudLoggingInput,
    QueryCloudRunServicesInput,
    QueryComputeInstancesInput,
    QueryIamPolicyInput,
    QueryStorageBucketsInput,
    ToolExecutionStatus,
    TtsSynthesisRequest,
)
from software_factory.security import IapVerifier
from software_factory.tools import (
    query_cloud_logging_readonly,
    query_cloud_run_services_readonly,
    query_compute_instances_readonly,
    query_iam_policy_readonly,
    query_storage_buckets_readonly,
)
from software_factory.api.server import create_software_factory_api


@pytest.fixture
def test_client() -> TestClient:
    cfg = FactoryConfig(
        app_name="test_ge_cloud_chat",
        project_id="test-proj-509515",
        iap_enforce=False,
        authorized_users=["joshholtz@google.com", "*@google.com"],
    )
    api = create_software_factory_api(cfg)
    return TestClient(api)


# ==============================================================================
# 1. Identity-Aware Proxy (IAP) Tests
# ==============================================================================
def test_iap_verifier_authorized_user():
    cfg = FactoryConfig(authorized_users=["joshholtz@google.com", "*@corp.google.com"])
    verifier = IapVerifier(cfg)
    assert verifier.is_user_authorized("joshholtz@google.com") is True
    assert verifier.is_user_authorized("alice@corp.google.com") is True
    assert verifier.is_user_authorized("attacker@malicious.com") is False


def test_iap_endpoint_user_profile(test_client: TestClient):
    # Simulated IAP header
    res = test_client.get(
        "/api/v1/me",
        headers={
            "X-Goog-Authenticated-User-Email": "accounts.google.com:joshholtz@google.com",
            "X-Goog-Authenticated-User-Id": "accounts.google.com:1029384756",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "joshholtz@google.com"
    assert data["verified"] is True
    assert "roles/iap.httpsResourceAccessor" in data["roles"]


def test_iap_enforced_missing_headers_blocked():
    cfg = FactoryConfig(iap_enforce=True, authorized_users=["*@google.com"])
    api = create_software_factory_api(cfg)
    client = TestClient(api)

    # Missing IAP headers in enforced environment
    res = client.get("/api/v1/me")
    assert res.status_code == 401
    err = res.json()["detail"]
    assert err["error_code"] == "IAP_AUTHENTICATION_REQUIRED"


def test_iap_enforced_unauthorized_user_blocked():
    cfg = FactoryConfig(iap_enforce=False, authorized_users=["*@google.com"])
    api = create_software_factory_api(cfg)
    client = TestClient(api)

    res = client.get(
        "/api/v1/me",
        headers={"X-Goog-Authenticated-User-Email": "accounts.google.com:external@unauthorized.org"},
    )
    assert res.status_code == 403
    err = res.json()["detail"]
    assert err["error_code"] == "IAP_USER_NOT_AUTHORIZED"


# ==============================================================================
# 2. Strict Database Access Restriction Guardrail Tests
# ==============================================================================
def test_database_query_blocker_sql_injection():
    guard = DatabaseAccessBlockerGuardrail()

    # Direct SQL query attempt
    allowed, reason, remediation = guard.check_query_allowed(
        "SELECT * FROM users WHERE active = true"
    )
    assert allowed is False
    assert "strictly prohibited" in reason
    assert any("infrastructure" in step for step in remediation)


def test_database_query_blocker_cloud_sql_and_spanner():
    guard = DatabaseAccessBlockerGuardrail()

    allowed_sql, _, _ = guard.check_query_allowed(
        "Can you query the cloud sql postgres database to dump customer records?"
    )
    assert allowed_sql is False

    allowed_spanner, _, _ = guard.check_query_allowed(
        "Inspect the Spanner orders table and show records"
    )
    assert allowed_spanner is False

    allowed_firestore, _, _ = guard.check_query_allowed(
        "Query the firestore documents in the payments collection"
    )
    assert allowed_firestore is False


def test_database_guardrail_cloud_logging_allowed():
    guard = DatabaseAccessBlockerGuardrail()

    # Querying Cloud Logging for database logs is explicitly permitted
    allowed, reason, _ = guard.check_query_allowed(
        "Check Cloud Logging for postgres connection error logs"
    )
    assert allowed is True
    assert "explicitly permitted" in reason


# ==============================================================================
# 3. Read-Only Cloud Environment Tools Tests
# ==============================================================================
def test_query_compute_instances_tool():
    res = query_compute_instances_readonly({"project_id": "l200-509515"})
    assert res.get("status") in ("success", "error")
    assert res.get("data", {}).get("resource_domain") == "compute_instances"
    assert "summary" in res


def test_query_cloud_run_services_tool():
    res = query_cloud_run_services_readonly({"project_id": "l200-509515", "region": "us-central1"})
    assert res.get("status") in ("success", "error")
    assert res.get("data", {}).get("resource_domain") == "cloud_run_services"
    assert "summary" in res


def test_query_storage_buckets_tool():
    res = query_storage_buckets_readonly({"project_id": "l200-509515"})
    assert res.get("status") in ("success", "error")
    assert res.get("data", {}).get("resource_domain") == "storage_buckets"
    assert "summary" in res


def test_query_iam_policy_tool():
    res = query_iam_policy_readonly({"project_id": "l200-509515"})
    assert res.get("status") in ("success", "error")
    assert res.get("data", {}).get("resource_domain") == "service_accounts"
    assert "summary" in res


def test_query_cloud_logging_tool():
    res = query_cloud_logging_readonly(
        {"severity": "ERROR", "max_entries": 5, "target_project_id": "l200-509515"}
    )
    assert res.get("status") in ("success", "error")
    assert "summary" in res


# ==============================================================================
# 4. Text-to-Speech (TTS) Voice Engine Tests
# ==============================================================================
def test_clean_markdown_for_speech():
    raw_md = """
    ### Summary
    Here is a **critical** observation from `us-central1`:
    - Instance-1 is RUNNING
    | Instance | Zone |
    |---|---|
    | vm-1 | us-central1-a |
    ```bash
    gcloud compute instances list
    ```
    Please check [Cloud Console](https://console.cloud.google.com).
    """
    cleaned = clean_markdown_for_speech(raw_md)
    assert "###" not in cleaned
    assert "**" not in cleaned
    assert "gcloud compute" not in cleaned
    assert "Table details summarized in text." in cleaned
    assert "critical" in cleaned


@pytest.mark.asyncio
async def test_tts_service_synthesis():
    req = TtsSynthesisRequest(
        text="Welcome to Gemini Enterprise Cloud Chat. All systems operational.",
        voice_name="en-US-Journey-F",
    )
    res = await DEFAULT_TTS_SERVICE.synthesize(req)
    assert res.audio_base64 is not None
    assert len(res.audio_base64) > 100
    assert res.audio_content_type in ("audio/mp3", "audio/wav")
    # Verify valid base64
    decoded = base64.b64decode(res.audio_base64)
    assert len(decoded) > 50


def test_tts_endpoint(test_client: TestClient):
    res = test_client.post(
        "/api/v1/tts",
        json={"text": "Cloud Run service is healthy.", "voice_name": "en-US-Journey-F"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "audio_base64" in data
    assert data["audio_content_type"] in ("audio/mp3", "audio/wav")


# ==============================================================================
# 5. Full Conversational Flow & Frontend Tests
# ==============================================================================
def test_gemini_enterprise_frontend_served(test_client: TestClient):
    res = test_client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "Gemini Enterprise" in res.text
    assert "Cloud Infrastructure Assistant" in res.text
    assert "chatInput" in res.text
    assert "btn-mic" in res.text


def test_cloud_chat_endpoint_normal_query(test_client: TestClient):
    res = test_client.post(
        "/api/v1/chat",
        headers={"X-Goog-Authenticated-User-Email": "accounts.google.com:joshholtz@google.com"},
        json={
            "message": "List active Compute VMs and status",
            "session_id": "test-session-1",
            "enable_tts": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["user_email"] == "joshholtz@google.com"
    assert data["database_blocked"] is False
    assert "query_compute_instances_readonly" in data["resource_queries_executed"]
    assert "audio_base64" in data
    assert data["audio_base64"] is not None


def test_cloud_chat_endpoint_database_blocked(test_client: TestClient):
    res = test_client.post(
        "/api/v1/chat",
        headers={"X-Goog-Authenticated-User-Email": "accounts.google.com:joshholtz@google.com"},
        json={
            "message": "SELECT id, password_hash FROM users in postgres cloud sql",
            "session_id": "test-session-2",
            "enable_tts": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["database_blocked"] is True
    assert "Enterprise Security Policy Refusal" in data["reply"]
    assert "Cloud Logging" in data["reply"]
    # TTS voice should articulate the refusal
    assert data["audio_base64"] is not None
