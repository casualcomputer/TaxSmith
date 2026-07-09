"""Retrieval interfaces and ranking helpers."""

from __future__ import annotations

from typing import Protocol

from taxsmith.schemas import RetrievalRequest, RetrievalResult, TaxQuery, WorkflowId
from taxsmith.workflow_contracts import WORKFLOW_CONTRACTS


class Retriever(Protocol):
    def retrieve(self, request: RetrievalRequest) -> list[RetrievalResult]:
        """Return authority-aware retrieval results."""


def build_retrieval_request(query: TaxQuery, workflow_id: WorkflowId) -> RetrievalRequest:
    contract = WORKFLOW_CONTRACTS[workflow_id]
    required_sources = (
        contract.required_exact_lookups
        + contract.required_cra_sources
        + contract.required_forms
        + contract.required_case_principles
    )
    return RetrievalRequest(
        query=query,
        workflow_id=workflow_id,
        required_sources=required_sources,
        optional_sources=contract.conditional_checks,
        missing_fact_questions=contract.missing_fact_questions,
    )


def rank_results(results: list[RetrievalResult]) -> list[RetrievalResult]:
    return sorted(results, key=lambda result: result.combined_score, reverse=True)


def missing_required_sources(request: RetrievalRequest, results: list[RetrievalResult]) -> list[str]:
    found_text = " ".join(
        [
            result.chunk.title
            + " "
            + (result.chunk.citation.section or "")
            + " "
            + " ".join(result.chunk.related_sections)
            + " "
            + " ".join(result.chunk.related_forms)
            for result in results
        ]
    ).lower()
    return [source for source in request.required_sources if source.lower() not in found_text]
