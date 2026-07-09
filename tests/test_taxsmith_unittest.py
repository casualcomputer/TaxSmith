from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from taxsmith.retrieval import build_retrieval_request, missing_required_sources, rank_results
from taxsmith.agent import analyze_question
from taxsmith.classifier import classify_workflow
from taxsmith.schemas import (
    AUTHORITY_RANK,
    AuthorityType,
    Citation,
    RetrievalResult,
    SourceStatus,
    TaxChunk,
    TaxQuery,
    WorkflowId,
)
from taxsmith.workflow_contracts import WORKFLOW_CONTRACTS


def load_build_corpus_layout_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build_corpus_layout.py"
    spec = importlib.util.spec_from_file_location("build_corpus_layout", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_corpus_layout"] = module
    spec.loader.exec_module(module)
    return module


class WorkflowContractTests(unittest.TestCase):
    def test_all_mvp_contracts_have_required_sources_and_guardrails(self) -> None:
        self.assertGreaterEqual(len(WORKFLOW_CONTRACTS), 10)
        for contract in WORKFLOW_CONTRACTS.values():
            with self.subTest(contract=contract.workflow_id.value):
                self.assertTrue(contract.required_exact_lookups)
                self.assertTrue(contract.required_cra_sources)
                self.assertTrue(contract.missing_fact_questions)
                self.assertTrue(contract.human_review_triggers)

    def test_section_85_contract_requires_form_and_admin_guidance(self) -> None:
        request = build_retrieval_request(
            TaxQuery("I want to transfer appreciated shares to my holdco."),
            WorkflowId.SECTION_85_ROLLOVER,
        )

        self.assertIn("ITA 85(1)", request.required_sources)
        self.assertIn("IC76-19R3", request.required_sources)
        self.assertIn("T2057", request.required_sources)

    def test_authority_ranking_prioritizes_law_over_cra_guidance(self) -> None:
        law_result = RetrievalResult(
            chunk=TaxChunk(
                chunk_id="ita-85",
                title="Income Tax Act subsection 85(1)",
                text="Election rule.",
                citation=Citation(
                    title="Income Tax Act",
                    url="https://laws-lois.justice.gc.ca/eng/acts/I-3.3/",
                    authority_type=AuthorityType.LAW,
                    status=SourceStatus.CURRENT,
                    section="85(1)",
                ),
            ),
            lexical_score=0.2,
            vector_score=0.2,
        )
        cra_result = RetrievalResult(
            chunk=TaxChunk(
                chunk_id="ic76-19",
                title="IC76-19R3",
                text="Administrative guidance.",
                citation=Citation(
                    title="IC76-19R3",
                    url="https://www.canada.ca/",
                    authority_type=AuthorityType.CRA_INTERPRETATION,
                    status=SourceStatus.CURRENT,
                ),
            ),
            lexical_score=0.9,
            vector_score=0.9,
        )

        ranked = rank_results([cra_result, law_result])
        self.assertEqual(ranked[0].chunk.citation.authority_type, AuthorityType.LAW)
        self.assertGreater(law_result.authority_score, cra_result.authority_score)

    def test_court_authority_ranking_keeps_federal_court_separate(self) -> None:
        self.assertGreater(AUTHORITY_RANK[AuthorityType.FCA_CASE], AUTHORITY_RANK[AuthorityType.FC_CASE])
        self.assertGreater(AUTHORITY_RANK[AuthorityType.FC_CASE], AUTHORITY_RANK[AuthorityType.TCC_CASE])

    def test_missing_required_sources_reports_contract_gaps(self) -> None:
        request = build_retrieval_request(TaxQuery("rollover"), WorkflowId.SECTION_85_ROLLOVER)
        result = RetrievalResult(
            chunk=TaxChunk(
                chunk_id="only-ita-85",
                title="ITA 85(1)",
                text="Rollover provision.",
                citation=Citation(
                    title="Income Tax Act",
                    url="https://laws-lois.justice.gc.ca/eng/acts/I-3.3/",
                    authority_type=AuthorityType.LAW,
                    section="85(1)",
                ),
                related_sections=("ITA 85(1)",),
            )
        )

        missing = missing_required_sources(request, [result])
        self.assertIn("IC76-19R3", missing)
        self.assertIn("T2057", missing)

    def test_classifier_routes_section_116_query(self) -> None:
        workflow_id, matched = classify_workflow(
            "A non-resident is selling Canadian private company shares. Do we need a T2062?"
        )

        self.assertEqual(workflow_id, WorkflowId.SECTION_116_TCP)
        self.assertIn("non-resident", matched)

    def test_agent_returns_live_trace_without_ollama(self) -> None:
        result = analyze_question(
            TaxQuery("Can we deduct interest after refinancing shareholder advances?")
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["workflow_id"], WorkflowId.INTEREST_DEDUCTIBILITY.value)
        self.assertIn("Classified prompt", result["trace"][0])
        self.assertIn("Required law/regulation checks", result["answer"])


class UiPrototypeTests(unittest.TestCase):
    def test_static_ui_contains_every_contract_label(self) -> None:
        app_js = Path("site/app.js").read_text(encoding="utf-8")
        for contract in WORKFLOW_CONTRACTS.values():
            with self.subTest(label=contract.label):
                self.assertIn(contract.label, app_js)

    def test_static_ui_files_exist(self) -> None:
        for path in ("site/index.html", "site/styles.css", "site/app.js"):
            with self.subTest(path=path):
                self.assertTrue(Path(path).exists())


class CorpusMetadataTests(unittest.TestCase):
    def test_document_size_metadata_includes_token_estimate(self) -> None:
        module = load_build_corpus_layout_module()
        metadata = module.document_size_metadata("one two three\nfour")

        self.assertEqual(metadata["character_count"], 18)
        self.assertEqual(metadata["line_count"], 2)
        self.assertEqual(metadata["word_count"], 4)
        self.assertEqual(metadata["estimated_token_count"], 5)
        self.assertEqual(metadata["token_estimator"], "ceil_character_count_div_4")


if __name__ == "__main__":
    unittest.main()
