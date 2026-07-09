"""Orchestration boundary.

LangGraph belongs here: it should coordinate workflow classification,
mandatory retrieval, source-status checks, citation verification, missing-fact
analysis, and final answer drafting.

The retrieval layer stays framework-agnostic so benchmark tests can run without
agent execution.
"""

from __future__ import annotations

from dataclasses import dataclass

from taxsmith.retrieval import Retriever, build_retrieval_request, missing_required_sources, rank_results
from taxsmith.schemas import RetrievalResult, TaxQuery, WorkflowId


@dataclass(frozen=True)
class OrchestrationDraft:
    workflow_id: WorkflowId
    ranked_results: tuple[RetrievalResult, ...]
    missing_required_sources: tuple[str, ...]
    missing_fact_questions: tuple[str, ...]
    human_review_triggers: tuple[str, ...]


def draft_research_packet(
    query: TaxQuery,
    workflow_id: WorkflowId,
    retriever: Retriever,
) -> OrchestrationDraft:
    request = build_retrieval_request(query, workflow_id)
    results = rank_results(retriever.retrieve(request))
    return OrchestrationDraft(
        workflow_id=workflow_id,
        ranked_results=tuple(results),
        missing_required_sources=tuple(missing_required_sources(request, results)),
        missing_fact_questions=request.missing_fact_questions,
        human_review_triggers=tuple(request.optional_sources),
    )
