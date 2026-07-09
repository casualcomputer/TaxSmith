import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from taxsmith.retrieval import build_retrieval_request
from taxsmith.schemas import TaxQuery, WorkflowId
from taxsmith.workflow_contracts import WORKFLOW_CONTRACTS


def test_section_85_contract_requires_form_and_admin_guidance() -> None:
    request = build_retrieval_request(
        TaxQuery("I want to transfer appreciated shares to my holdco."),
        WorkflowId.SECTION_85_ROLLOVER,
    )

    assert "ITA 85(1)" in request.required_sources
    assert "IC76-19R3" in request.required_sources
    assert "T2057" in request.required_sources


def test_mvp_contracts_have_missing_fact_questions() -> None:
    for contract in WORKFLOW_CONTRACTS.values():
        assert contract.missing_fact_questions
