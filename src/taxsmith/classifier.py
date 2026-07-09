"""Rule-based workflow classifier for the prototype agent.

The classifier is intentionally simple and inspectable. Model-based routing can
replace or augment this once the benchmark exists.
"""

from __future__ import annotations

from taxsmith.schemas import WorkflowId


WORKFLOW_KEYWORDS: dict[WorkflowId, tuple[str, ...]] = {
    WorkflowId.SECTION_85_ROLLOVER: (
        "85",
        "rollover",
        "t2057",
        "t2058",
        "holdco",
        "transfer appreciated",
        "elected amount",
    ),
    WorkflowId.SECTION_116_TCP: (
        "116",
        "t2062",
        "non-resident",
        "taxable canadian property",
        "certificate of compliance",
        "withhold",
        "withholding",
    ),
    WorkflowId.SHAREHOLDER_LOAN: (
        "shareholder loan",
        "loan account",
        "debit shareholder",
        "15(2)",
        "80.4",
        "advance",
        "repaid",
    ),
    WorkflowId.SHAREHOLDER_BENEFIT: (
        "shareholder benefit",
        "personal expense",
        "renovation",
        "corporate property",
        "15(1)",
        "benefit conferred",
    ),
    WorkflowId.EMPLOYEE_VS_CONTRACTOR: (
        "contractor",
        "employee",
        "self-employed",
        "payroll",
        "cpp",
        "ei",
        "t4a",
    ),
    WorkflowId.PRINCIPAL_RESIDENCE: (
        "principal residence",
        "t2091",
        "home",
        "condo",
        "rented",
        "change in use",
    ),
    WorkflowId.T1135_FOREIGN_REPORTING: (
        "t1135",
        "specified foreign property",
        "foreign reporting",
        "foreign assets",
        "us brokerage",
    ),
    WorkflowId.OBJECTIONS_APPEALS: (
        "objection",
        "appeal",
        "reassessment",
        "notice of assessment",
        "tax court",
        "deadline",
    ),
    WorkflowId.TRUST_T3_REPORTING: (
        "trust",
        "t3",
        "schedule 15",
        "beneficiary",
        "bare trust",
        "21-year",
    ),
    WorkflowId.INTEREST_DEDUCTIBILITY: (
        "interest",
        "borrowed",
        "loan",
        "20(1)(c)",
        "deduct",
        "refinance",
        "dividend",
    ),
}


def classify_workflow(text: str) -> tuple[WorkflowId, list[str]]:
    normalized = text.lower()
    scores: dict[WorkflowId, int] = {}
    matched: dict[WorkflowId, list[str]] = {}

    for workflow_id, keywords in WORKFLOW_KEYWORDS.items():
        hits = [keyword for keyword in keywords if keyword in normalized]
        if hits:
            scores[workflow_id] = len(hits)
            matched[workflow_id] = hits

    if not scores:
        return WorkflowId.UNKNOWN, []

    workflow_id = max(scores, key=lambda candidate: scores[candidate])
    return workflow_id, matched[workflow_id]
