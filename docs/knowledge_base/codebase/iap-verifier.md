---
okf_version: "1.0"
entry_id: "iap-verifier"
entry_name: "Identity-Aware Proxy (IAP) Verification Layer"
category: "codebase"
sub_category: "security_and_auth"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Security Architecture / Academy L200"
dendrite_node_id: "iap_gateway"
discovered_by: "static_analysis"
last_verified: "2026-09-29"
---

# OKF (Codebase): Identity-Aware Proxy (IAP) Verification Layer

## 1. Executive Summary & Purpose
- **Primary Function**: Enforces zero-trust authentication and caller authorization on all incoming requests to the Gemini Enterprise Cloud Chat Agent using Google Cloud Identity-Aware Proxy headers (`X-Goog-Authenticated-User-Email` and `X-Goog-IAP-JWT-Assertion`).
- **Target Audience / Consumer**: All web frontend users, automated agents, and external API clients invoking `/api/v1/chat` and `/api/v1/me`.
- **Key Outcome**: Guarantees that only authorized users granted `roles/iap.httpsResourceAccessor` or matching authorized caller patterns can interact with the cloud environment; rejects unauthenticated callers with HTTP 401 and unauthorized callers with HTTP 403.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `Zone1_Perimeter` & `Zone2_AgentEngine` boundary gate.
- **Inbound Connections**: `ge_frontend` and external HTTP clients sending signed IAP headers.
- **Outbound Connections**: Passes verified `IapUserIdentity` to `cloud_chat_agent` and `focal_coordinator_agent`.
- **Trust Boundary & Security Classification**: Zero-trust gateway; extracts Google account identity and checks cryptographic JWT signatures against Google's public key certificate endpoints.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Verifier module: [`software_factory/security/iap_verifier.py`](../../../software_factory/security/iap_verifier.py)
  - Security export: [`software_factory/security/__init__.py`](../../../software_factory/security/__init__.py)
  - Schemas: [`IapUserIdentity` in `software_factory/schemas/models.py`](../../../software_factory/schemas/models.py)
- **Protocols & Interfaces**: HTTP header extraction (`X-Goog-Authenticated-User-Email`, `X-Goog-IAP-JWT-Assertion`), ES256 JWT decoding, OpenTelemetry span `security.verify_iap_request`.
- **Configuration & Environment Variables**:
  - `IAP_ENFORCE`: Boolean flag (`true` to strictly require valid JWT assertions; `false` for offline dev simulation).
  - `IAP_EXPECTED_AUDIENCE`: Optional GCP audience string (`/projects/{project_number}/global/backendServices/{backend_id}`).
  - `AUTHORIZED_USERS`: Comma-separated list of authorized email addresses or wildcards (`joshholtz@google.com,*@google.com`).

## 4. Operational Runbook & Lifecycle
- **Usage & Dependency Injection**:
  ```python
  from software_factory.security import verify_iap_user
  @app.get("/protected")
  async def route(identity: IapUserIdentity = Depends(verify_iap_user)):
      return identity
  ```
- **Verification & Health Checks**:
  ```bash
  ./bin/uv run pytest tests/test_ge_cloud_chat_suite.py -k "test_iap"
  ```
- **Failure Modes & Blast Radius**:
  - Missing IAP headers trigger HTTP 401 with `IAP_AUTHENTICATION_REQUIRED` and remediation instructions.
  - Unauthorized domain/caller triggers HTTP 403 with `IAP_USER_NOT_AUTHORIZED` and remediation instructions.

## 5. References & Linked Assets
- Google Cloud IAP Documentation: [https://cloud.google.com/iap/docs/signed-headers-howto](https://cloud.google.com/iap/docs/signed-headers-howto)
- Dendrite model: [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
