"""Prototype workflow agent.

This module runs a live workflow trace. It can optionally ask Ollama to draft an
answer, but the legal workflow contract remains deterministic and visible.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import asdict
from typing import Any

from taxsmith.classifier import classify_workflow
from taxsmith.schemas import TaxQuery, WorkflowId
from taxsmith.workflow_contracts import WORKFLOW_CONTRACTS, WorkflowContract


ANSWER_BACKBONE = (
    "Issue classification",
    "Short answer with confidence",
    "Authority-ranked law and regulations",
    "CRA administrative position",
    "Forms, elections, and deadlines",
    "Cases and hierarchy notes",
    "Missing facts",
    "Risk flags and human-review trigger",
)


def contract_to_payload(contract: WorkflowContract) -> dict[str, Any]:
    return {
        "workflow_id": contract.workflow_id.value,
        "label": contract.label,
        "law": list(contract.required_exact_lookups),
        "cra": list(contract.required_cra_sources),
        "forms": list(contract.required_forms),
        "cases": list(contract.required_case_principles),
        "conditional": list(contract.conditional_checks),
        "missing_facts": list(contract.missing_fact_questions),
        "human_review_triggers": list(contract.human_review_triggers),
    }


def build_deterministic_draft(prompt: str, contract: WorkflowContract, matched_terms: list[str]) -> str:
    law = ", ".join(contract.required_exact_lookups)
    cra = ", ".join(contract.required_cra_sources)
    forms = ", ".join(contract.required_forms) or "no mandatory form in this contract"
    review = "; ".join(contract.human_review_triggers)
    missing = "\n".join([f"- {question}" for question in contract.missing_fact_questions])
    terms = ", ".join(matched_terms) or "workflow keyword match"

    return (
        f"Classified as: {contract.label}.\n\n"
        f"Why: matched {terms}.\n\n"
        f"Required law/regulation checks: {law}.\n"
        f"CRA/practical guidance to retrieve separately: {cra}.\n"
        f"Forms/deadlines to check: {forms}.\n\n"
        "Missing facts to ask before confidence:\n"
        f"{missing}\n\n"
        f"Human-review triggers: {review}.\n\n"
        "This is a live workflow trace, not a final tax opinion. The next build step is to connect "
        "these required source slots to indexed source text and citation verification."
    )


def build_ollama_prompt(user_prompt: str, contract: WorkflowContract, matched_terms: list[str]) -> str:
    payload = contract_to_payload(contract)
    return (
        "You are Taxsmith, an authority-aware Canadian tax workflow assistant.\n"
        "Draft a cautious triage answer using ONLY the workflow contract below. "
        "Do not invent citations, forms, cases, or law. Do not treat CRA guidance as law. "
        "Emphasize missing facts and human-review triggers. Keep it concise.\n\n"
        f"User prompt:\n{user_prompt}\n\n"
        f"Matched routing terms: {matched_terms}\n\n"
        f"Workflow contract JSON:\n{json.dumps(payload, indent=2)}\n\n"
        "Required answer sections:\n"
        "1. Issue classification\n"
        "2. What must be checked\n"
        "3. Missing facts\n"
        "4. Risk flags\n"
        "5. Confidence / review trigger\n"
    )


def call_ollama(
    *,
    base_url: str,
    model: str,
    user_prompt: str,
    contract: WorkflowContract,
    matched_terms: list[str],
    timeout_seconds: float = 45,
) -> tuple[str, str]:
    url = base_url.rstrip("/") + "/api/chat"
    body = {
        "model": model,
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": build_ollama_prompt(user_prompt, contract, matched_terms),
            }
        ],
        "options": {"temperature": 0.1},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return "", f"Ollama unavailable: {exc}"

    content = data.get("message", {}).get("content", "")
    if not content:
        return "", "Ollama returned no message content."
    return content, "Ollama draft generated."


def analyze_question(
    query: TaxQuery,
    *,
    use_ollama: bool = False,
    ollama_base_url: str = "http://127.0.0.1:11434",
    ollama_model: str = "qwen3",
) -> dict[str, Any]:
    workflow_id, matched_terms = classify_workflow(query.text)
    if workflow_id == WorkflowId.UNKNOWN:
        return {
            "status": "needs_routing_review",
            "workflow_id": WorkflowId.UNKNOWN.value,
            "label": "Unknown workflow",
            "matched_terms": [],
            "trace": [
                "No workflow contract matched confidently.",
                "Ask a tax professional or add a narrower workflow before answering.",
            ],
            "answer": "I could not confidently route this question to one of the MVP workflow contracts.",
            "contract": None,
            "answer_backbone": list(ANSWER_BACKBONE),
            "ollama_status": "not_called",
        }

    contract = WORKFLOW_CONTRACTS[workflow_id]
    trace = [
        f"Classified prompt as {contract.label}.",
        f"Matched routing terms: {', '.join(matched_terms)}.",
        f"Scheduled {len(contract.required_exact_lookups)} exact law/regulation lookups.",
        f"Scheduled {len(contract.required_cra_sources)} CRA/practical guidance checks.",
        f"Scheduled {len(contract.required_forms)} form/deadline checks.",
        f"Prepared {len(contract.missing_fact_questions)} missing-fact questions.",
        f"Prepared {len(contract.human_review_triggers)} human-review trigger checks.",
    ]

    answer = build_deterministic_draft(query.text, contract, matched_terms)
    ollama_status = "not_called"
    if use_ollama:
        ollama_answer, ollama_status = call_ollama(
            base_url=ollama_base_url,
            model=ollama_model,
            user_prompt=query.text,
            contract=contract,
            matched_terms=matched_terms,
        )
        if ollama_answer:
            answer = ollama_answer

    return {
        "status": "ok",
        "workflow_id": workflow_id.value,
        "label": contract.label,
        "matched_terms": matched_terms,
        "trace": trace,
        "answer": answer,
        "contract": contract_to_payload(contract),
        "answer_backbone": list(ANSWER_BACKBONE),
        "ollama_status": ollama_status,
    }
