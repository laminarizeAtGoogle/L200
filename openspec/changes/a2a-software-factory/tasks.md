# Tasks: A2A Agent Graph Software Factory

- [x] 1. Implement strict Pydantic schemas (`software_factory/schemas/models.py`) and system constitutions (`software_factory/prompts/constitutions.py`).
- [x] 2. Implement observability & security layer: PII redaction (`pii_redaction.py`), OpenTelemetry tracing (`telemetry.py`), structured JSON logging (`structured_logging.py`), Intent-vs-Outcome capture (`intent_outcome.py`), and Secret Manager vault (`secret_manager.py`).
- [x] 3. Implement context & memory layer: ADK compaction & sliding-window compactor (`compaction.py`), persistent SQLite/Vertex session & vector memory store (`persistent_store.py`), and non-blocking async memory consolidator (`async_memory.py`).
- [x] 4. Implement orchestration layer: `StrategicModelRouter` (`model_router.py`), `HumanInTheLoopGate` (`hitl_hooks.py`), and `SoftwareFactoryGuardrailsPlugin` (`guardrails_plugin.py`).
- [x] 5. Implement 11 schema-validated tools across `workspace_tools.py`, `git_wif_tools.py`, and `gcloud_probe_tools.py`.
- [x] 6. Implement ADK multi-agent graph (`subagents.py`, `focal_agent.py`), A2A mesh (`a2a_mesh.py`), and unified FastAPI + A2A server (`server.py`, `main.py`).
- [x] 7. Populate Argolis Terraform infrastructure (`terraform/main.tf`, `terraform/variables.tf`, `terraform/outputs.tf`) and automated evaluation suite (`evals/`, `tests/`, `.github/workflows/agent-eval-and-test.yml`).
- [x] 8. Synchronize Mermaid architecture diagram (`docs/architecture_diagram.mmd`, `docs/architecture.md`) and Google OKF Knowledge Base (`docs/knowledge_base/`).
