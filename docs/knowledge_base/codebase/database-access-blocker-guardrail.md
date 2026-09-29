---
okf_version: "1.0"
entry_id: "database-access-blocker-guardrail"
entry_name: "Database Access Restriction Guardrail"
category: "codebase"
sub_category: "guardrails_and_policies"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Security Architecture / Academy L200"
dendrite_node_id: "db_quarantine_barrier"
discovered_by: "static_analysis"
last_verified: "2026-09-29"
---

# OKF (Codebase): Database Access Restriction Guardrail

## 1. Executive Summary & Purpose
- **Primary Function**: Enforces strict isolation between the read-only AI agent and internal application databases (Cloud SQL, Spanner, Firestore, Bigtable, BigQuery customer tables), blocking any SQL or database inspection queries while explicitly permitting Cloud Logging systems.
- **Target Audience / Consumer**: Cloud Chat Agent and Focal Coordinator runtime.
- **Key Outcome**: Guarantees zero leakage of proprietary application database records, table schemas, or customer data; guides users to Cloud Logging if they are seeking diagnostic or error traces.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `Zone2_AgentEngine` boundary wall between Agent and `internal_databases`.
- **Inbound Connections**: Evaluates user prompts in `handle_cloud_chat` and intercepts tool call attempts.
- **Outbound Connections**: Emits `DATABASE_ACCESS_ATTEMPT_BLOCKED` security events to structured logging and returns guided policy refusals.
- **Trust Boundary & Security Classification**: Critical security boundary; prevents SQL injection, data exfiltration, and unauthorized data plane access.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Guardrail class: [`software_factory/orchestration/database_guardrail.py`](../../../software_factory/orchestration/database_guardrail.py)
  - System Constitution: [`software_factory/prompts/constitutions.py`](../../../software_factory/prompts/constitutions.py) (`GEMINI_ENTERPRISE_CLOUD_CHAT_CONSTITUTION`)
- **Detection Engine**: Regex and keyword classifier targeting SQL verbs (`SELECT`, `INSERT`, `UPDATE`), database products (`Cloud SQL`, `Postgres`, `Spanner`, `Firestore`), while recognizing Cloud Logging keywords (`Cloud Logging`, `error logs`, `traces`, `syslog`) as authorized exceptions.
- **Error Codes**: `POLICY_DATABASE_ACCESS_FORBIDDEN` with guided remediation instructions.

## 4. Operational Runbook & Lifecycle
- **Usage**:
  ```python
  from software_factory.orchestration.database_guardrail import DEFAULT_DATABASE_GUARDRAIL
  is_allowed, reason, remediation = DEFAULT_DATABASE_GUARDRAIL.check_query_allowed(prompt)
  ```
- **Verification & Health Checks**:
  ```bash
  ./bin/uv run pytest tests/test_ge_cloud_chat_suite.py -k "test_database_query_blocker"
  ```
- **Failure Modes & Blast Radius**:
  - Any prompt containing database query patterns is intercepted immediately before dispatching LLMs or tools, returning a standardized security refusal and TTS explanation.

## 5. References & Linked Assets
- Parent specification: [`AI in 5 Days Assessment Agent.md`](../../../AI%20in%205%20Days%20Assessment%20Agent.md)
- Agent coordinator: [`docs/knowledge_base/codebase/a2a-software-factory-api.md`](a2a-software-factory-api.md)
- Dendrite model: [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
