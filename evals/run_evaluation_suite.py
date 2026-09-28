#!/usr/bin/env python3
"""Automated Golden Dataset Evaluation Harness for the A2A Software Factory.

Executes the golden dataset (`evals/golden_dataset.evalset.json`) against the
Focal Conversational Coordinator and specialist sub-agents, statically measuring:
1. Tool Trajectory Accuracy (expected tools vs. actual executed tools)
2. Sub-Agent Orchestration Coverage
3. Strategic Model Routing Accuracy (Gemini Pro vs. Gemini Flash)
4. Security Guardrail & HITL Compliance
5. Output Rubric Keyword & PII Redaction Verification
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from software_factory.agents import (
    A2A_AGENT_ROUTES,
    FocalConversationOrchestrator,
)
from software_factory.memory import DEFAULT_ASYNC_CONSOLIDATOR
from software_factory.schemas import ChatMessageRequest


async def evaluate_golden_dataset(
    dataset_path: Path | None = None,
) -> dict[str, Any]:
    """Runs all golden evaluation cases and returns a structured score report."""
    path = dataset_path or (
        WORKSPACE_ROOT / "evals" / "golden_dataset.evalset.json"
    )
    dataset = json.loads(path.read_text(encoding="utf-8"))
    orchestrator = FocalConversationOrchestrator()

    case_results: list[dict[str, Any]] = []
    passed_cases = 0

    for case in dataset.get("eval_cases", []):
        eval_id = case["eval_id"]
        req = ChatMessageRequest(
            message=case["prompt"],
            session_id=f"eval-{eval_id}",
            user_id="eval-harness",
            workspace_path=str(WORKSPACE_ROOT),
            target_gcp_project_id=case.get("target_gcp_project_id"),
            target_github_repo=case.get("target_github_repo"),
        )
        response = await orchestrator.handle_chat(
            request=req,
            a2a_endpoints=A2A_AGENT_ROUTES,
        )

        actual_tools = [
            t.get("tool_name")
            for t in response.state.tool_executions
            if t.get("tool_name")
        ]
        expected_tools = case.get("expected_tools", [])
        tools_matched = all(t in actual_tools for t in expected_tools)

        expected_subagents = case.get("expected_subagents", [])
        subagents_matched = all(
            sa in response.state.invoked_subagents for sa in expected_subagents
        )

        expected_model = case.get("expected_routed_model")
        model_matched = (
            expected_model is None
            or response.state.routed_model == expected_model
        )

        expected_keywords = case.get("expected_keywords", [])
        keywords_matched = all(
            kw.lower() in response.reply.lower() for kw in expected_keywords
        )

        guardrail_code = case.get("expected_guardrail_code")
        guardrail_matched = True
        if guardrail_code:
            guardrail_matched = any(
                t.get("error_code") == guardrail_code
                for t in response.state.tool_executions
            )

        case_passed = (
            tools_matched
            and subagents_matched
            and model_matched
            and keywords_matched
            and guardrail_matched
        )
        if case_passed:
            passed_cases += 1

        case_results.append(
            {
                "eval_id": eval_id,
                "passed": case_passed,
                "routed_model": response.state.routed_model,
                "model_matched": model_matched,
                "expected_tools": expected_tools,
                "actual_tools": actual_tools,
                "tools_matched": tools_matched,
                "subagents_matched": subagents_matched,
                "keywords_matched": keywords_matched,
                "guardrail_matched": guardrail_matched,
            }
        )

    await DEFAULT_ASYNC_CONSOLIDATOR.flush_pending_tasks()

    total_cases = len(case_results)
    pass_rate = round(passed_cases / total_cases, 4) if total_cases else 0.0
    summary = {
        "eval_set_id": dataset.get("eval_set_id"),
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "pass_rate": pass_rate,
        "all_passed": passed_cases == total_cases,
        "results": case_results,
    }
    return summary


def main() -> None:
    report = asyncio.run(evaluate_golden_dataset())
    print(json.dumps(report, indent=2))
    if not report["all_passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
