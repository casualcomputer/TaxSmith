"""Core data structures for authority-aware tax retrieval.

These structures are intentionally dependency-free so the retrieval layer can be
tested without LangGraph, model SDKs, or a vector database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AuthorityType(str, Enum):
    LAW = "law"
    REGULATION = "regulation"
    TREATY = "treaty"
    SCC_CASE = "scc_case"
    FCA_CASE = "fca_case"
    FC_CASE = "fc_case"
    TCC_CASE = "tcc_case"
    CRA_INTERPRETATION = "cra_interpretation"
    CRA_ADMIN_PRACTICE = "cra_admin_practice"
    FORM = "form"
    GUIDE = "guide"
    FINANCE_PROPOSAL = "finance_proposal"
    SECONDARY = "secondary"
    USER_FACTS = "user_facts"


class SourceStatus(str, Enum):
    CURRENT = "current"
    HISTORICAL = "historical"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"
    REPLACED = "replaced"
    PROPOSED = "proposed"
    ENACTED_NOT_IN_FORCE = "enacted_not_in_force"
    IN_FORCE = "in_force"
    UNKNOWN = "unknown"


class WorkflowId(str, Enum):
    INTEREST_DEDUCTIBILITY = "interest_deductibility"
    SECTION_85_ROLLOVER = "section_85_rollover"
    SHAREHOLDER_LOAN = "shareholder_loan"
    SHAREHOLDER_BENEFIT = "shareholder_benefit"
    EMPLOYEE_VS_CONTRACTOR = "employee_vs_contractor"
    SECTION_116_TCP = "section_116_tcp"
    PRINCIPAL_RESIDENCE = "principal_residence"
    T1135_FOREIGN_REPORTING = "t1135_foreign_reporting"
    OBJECTIONS_APPEALS = "objections_appeals"
    TRUST_T3_REPORTING = "trust_t3_reporting"
    UNKNOWN = "unknown"


AUTHORITY_RANK: dict[AuthorityType, int] = {
    AuthorityType.LAW: 100,
    AuthorityType.REGULATION: 95,
    AuthorityType.TREATY: 93,
    AuthorityType.SCC_CASE: 90,
    AuthorityType.FCA_CASE: 85,
    AuthorityType.FC_CASE: 75,
    AuthorityType.TCC_CASE: 70,
    AuthorityType.CRA_INTERPRETATION: 60,
    AuthorityType.CRA_ADMIN_PRACTICE: 45,
    AuthorityType.FORM: 40,
    AuthorityType.GUIDE: 35,
    AuthorityType.FINANCE_PROPOSAL: 25,
    AuthorityType.SECONDARY: 10,
    AuthorityType.USER_FACTS: 0,
}


@dataclass(frozen=True)
class Citation:
    title: str
    url: str
    authority_type: AuthorityType
    status: SourceStatus = SourceStatus.UNKNOWN
    section: str | None = None
    paragraph: str | None = None
    publication_date: str | None = None
    effective_date_start: str | None = None
    effective_date_end: str | None = None


@dataclass(frozen=True)
class TaxChunk:
    chunk_id: str
    title: str
    text: str
    citation: Citation
    jurisdiction: str = "CA"
    tax_years: tuple[int, ...] = ()
    related_sections: tuple[str, ...] = ()
    related_forms: tuple[str, ...] = ()
    risk_tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaxQuery:
    text: str
    tax_year: int | None = None
    province: str | None = None
    taxpayer_type: str | None = None
    known_facts: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalRequest:
    query: TaxQuery
    workflow_id: WorkflowId
    required_sources: tuple[str, ...]
    optional_sources: tuple[str, ...] = ()
    missing_fact_questions: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalResult:
    chunk: TaxChunk
    lexical_score: float = 0.0
    vector_score: float = 0.0
    graph_score: float = 0.0

    @property
    def authority_score(self) -> int:
        return AUTHORITY_RANK[self.chunk.citation.authority_type]

    @property
    def combined_score(self) -> float:
        return (
            self.lexical_score * 0.35
            + self.vector_score * 0.35
            + self.graph_score * 0.20
            + self.authority_score * 0.10
        )
