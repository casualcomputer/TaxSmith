"""Deterministic workflow contracts for Canadian tax retrieval.

These contracts are the product's tax-specific spine. They define what must be
checked before an answer can claim to be practitioner-grade.
"""

from __future__ import annotations

from dataclasses import dataclass

from taxsmith.schemas import WorkflowId


@dataclass(frozen=True)
class WorkflowContract:
    workflow_id: WorkflowId
    label: str
    required_exact_lookups: tuple[str, ...]
    required_cra_sources: tuple[str, ...]
    required_forms: tuple[str, ...] = ()
    required_case_principles: tuple[str, ...] = ()
    conditional_checks: tuple[str, ...] = ()
    missing_fact_questions: tuple[str, ...] = ()
    human_review_triggers: tuple[str, ...] = ()


WORKFLOW_CONTRACTS: dict[WorkflowId, WorkflowContract] = {
    WorkflowId.INTEREST_DEDUCTIBILITY: WorkflowContract(
        workflow_id=WorkflowId.INTEREST_DEDUCTIBILITY,
        label="Interest deductibility",
        required_exact_lookups=("ITA 20(1)(c)", "ITA 18(1)(a)", "ITA 18(1)(b)", "ITA 67"),
        required_cra_sources=("CRA Folio S3-F6-C1",),
        required_forms=("T106 if non-arm's length non-resident interest", "NR4 if Part XIII reporting applies"),
        required_case_principles=("Shell", "Ludco", "Singleton"),
        conditional_checks=(
            "Thin capitalization / EIFEL if cross-border or group financing",
            "Part XIII withholding and treaty rate if non-resident lender",
            "Transfer pricing documentation if non-arm's length cross-border debt",
        ),
        missing_fact_questions=(
            "What was the direct current use of the borrowed money?",
            "Who is the lender and are the parties related or non-resident?",
            "Is there a legal obligation to pay interest?",
            "What taxation year applies?",
        ),
        human_review_triggers=(
            "Circular cash movements",
            "Related-party cross-border financing",
            "Aggressive surplus extraction or loss consolidation",
        ),
    ),
    WorkflowId.SECTION_85_ROLLOVER: WorkflowContract(
        workflow_id=WorkflowId.SECTION_85_ROLLOVER,
        label="Subsection 85 rollover",
        required_exact_lookups=("ITA 85(1)", "ITA 85(6)", "ITA 85(7)", "ITA 85(7.1)"),
        required_cra_sources=("IC76-19R3",),
        required_forms=("T2057", "T2058 if partnership transfer"),
        conditional_checks=(
            "ITA 84.1 if private corporation shares move to non-arm's length corporation",
            "ITA 55 if intercorporate dividends are part of the series",
            "ETA 167 if business assets are transferred",
            "Land transfer tax if real property is transferred",
        ),
        missing_fact_questions=(
            "Who are the transferor and transferee?",
            "Is the transferee a taxable Canadian corporation?",
            "What property is being transferred and what are FMV, ACB, UCC, liabilities, and elected amount?",
            "What are the filing due dates for all parties?",
        ),
        human_review_triggers=(
            "Private corporation share transfer to related corporation",
            "Valuation uncertainty",
            "Series involving dividends, redemptions, or sale to children/holdco",
        ),
    ),
    WorkflowId.SHAREHOLDER_BENEFIT: WorkflowContract(
        workflow_id=WorkflowId.SHAREHOLDER_BENEFIT,
        label="Shareholder benefit",
        required_exact_lookups=("ITA 15(1)", "ITA 15(2)", "ITA 80.4", "ITA 6", "ITA 69", "ITA 246"),
        required_cra_sources=("CRA Folio S3-F1-C1", "CRA Folio S3-F1-C2"),
        required_forms=("T4/T4A/T5 depending on characterization",),
        conditional_checks=(
            "Payroll remittances if employment compensation",
            "GST/HST consequences for personal use of corporate property",
            "Audit manual Chapter 24 as audit practice only",
        ),
        missing_fact_questions=(
            "What benefit was provided and to whom?",
            "Was the person acting as shareholder, employee, or both?",
            "Was there a written loan, lease, reimbursement, or shareholder account entry?",
            "What is the fair market value?",
        ),
        human_review_triggers=(
            "Weak valuation",
            "Large personal expenses in corporate books",
            "Year-end journal entries without legal support",
        ),
    ),
    WorkflowId.SHAREHOLDER_LOAN: WorkflowContract(
        workflow_id=WorkflowId.SHAREHOLDER_LOAN,
        label="Shareholder loan",
        required_exact_lookups=("ITA 15(2)", "ITA 80.4", "ITA 20(1)(j)"),
        required_cra_sources=("CRA Folio S3-F1-C1", "CRA Folio S3-F1-C2"),
        required_forms=("T2 shareholder account support", "T5/T4A if recharacterized"),
        conditional_checks=(
            "Repayment within statutory period",
            "Series of loans and repayments",
            "Prescribed-rate benefit calculation",
            "Payroll or dividend reporting if loan characterization fails",
        ),
        missing_fact_questions=(
            "Who received the loan and what is their shareholder/related status?",
            "When was the loan advanced and repaid, if repaid?",
            "Was there a written loan agreement and interest charged?",
            "Is there a series of advances and repayments?",
        ),
        human_review_triggers=(
            "Repeated year-end repayments and readvances",
            "No debtor-creditor documentation",
            "Large debit shareholder loan account",
        ),
    ),
    WorkflowId.EMPLOYEE_VS_CONTRACTOR: WorkflowContract(
        workflow_id=WorkflowId.EMPLOYEE_VS_CONTRACTOR,
        label="Employee vs contractor",
        required_exact_lookups=("ITA 5", "ITA 6", "ITA 8", "ITA 9", "ITA 153", "ITR 100", "ITR 102"),
        required_cra_sources=("CRA employment status guidance", "T4001"),
        required_forms=("TD1", "T4", "T4A", "CPT1 if CPP/EI ruling requested"),
        required_case_principles=("Sagaz", "Wiebe Door"),
        conditional_checks=(
            "CPP/EI pensionable and insurable employment",
            "GST/HST registration if genuinely self-employed",
            "Quebec payroll/social contribution rules if Quebec involved",
        ),
        missing_fact_questions=(
            "Who controls hours, tools, work location, substitution, and deliverables?",
            "Can the worker profit or suffer loss?",
            "Does actual conduct match the written contract?",
            "What province is involved?",
        ),
        human_review_triggers=("Mixed facts with significant retroactive payroll exposure",),
    ),
    WorkflowId.SECTION_116_TCP: WorkflowContract(
        workflow_id=WorkflowId.SECTION_116_TCP,
        label="Non-resident disposition of taxable Canadian property",
        required_exact_lookups=("ITA 2(3)", "ITA 115", "ITA 116", "ITA 248(1)", "ITA 54"),
        required_cra_sources=("IC72-17R6", "T4058"),
        required_forms=("T2062 series",),
        required_case_principles=("Alta Energy if treaty/GAAR issue is present",),
        conditional_checks=(
            "Treaty text, protocols, and MLI status",
            "Purchaser withholding liability",
            "GST/HST, UHT, and provincial land transfer taxes for real property",
        ),
        missing_fact_questions=(
            "What is the vendor's residence and treaty country?",
            "What property is being sold?",
            "Was a certificate obtained before closing?",
            "Do shares derive value principally from Canadian real/resource/timber property?",
        ),
        human_review_triggers=(
            "Treaty-protected property claim",
            "Private company shares with Canadian real property value",
            "Closing occurred without certificate",
        ),
    ),
    WorkflowId.PRINCIPAL_RESIDENCE: WorkflowContract(
        workflow_id=WorkflowId.PRINCIPAL_RESIDENCE,
        label="Principal residence exemption",
        required_exact_lookups=("ITA 40(2)(b)", "ITA 54", "ITA 45"),
        required_cra_sources=("CRA Folio S1-F3-C2",),
        required_forms=("T2091", "Schedule 3"),
        conditional_checks=(
            "Change-in-use election if rental/business use occurred",
            "Property flipping deeming rule if short holding period",
            "GST/HST if new/substantially renovated or business property",
            "Provincial real estate and vacancy/speculation tax issues",
        ),
        missing_fact_questions=(
            "Which years was the property ordinarily inhabited?",
            "Was any part rented or used for business?",
            "Was there a change in use?",
            "Were any other properties designated for the same years?",
        ),
        human_review_triggers=(
            "Mixed personal/rental/business use",
            "Multiple properties across the same years",
            "Sale shortly after acquisition",
        ),
    ),
    WorkflowId.T1135_FOREIGN_REPORTING: WorkflowContract(
        workflow_id=WorkflowId.T1135_FOREIGN_REPORTING,
        label="T1135 foreign reporting",
        required_exact_lookups=("ITA 233.3", "ITA 162(7)", "ITA 162(10)"),
        required_cra_sources=("CRA T1135 guidance",),
        required_forms=("T1135",),
        conditional_checks=(
            "Voluntary disclosures if missed filings exist",
            "Specified foreign property cost amount threshold",
            "Foreign affiliate reporting if T1134 may also apply",
        ),
        missing_fact_questions=(
            "What specified foreign property was held and what was the cost amount?",
            "Was the total cost amount over CAD 100,000 at any time in the year?",
            "Were any prior-year T1135 forms missed?",
            "Are any assets held through a corporation, trust, or partnership?",
        ),
        human_review_triggers=(
            "Multiple missed years",
            "Potential gross negligence penalty",
            "Foreign affiliate or trust structure involved",
        ),
    ),
    WorkflowId.OBJECTIONS_APPEALS: WorkflowContract(
        workflow_id=WorkflowId.OBJECTIONS_APPEALS,
        label="Objections and appeals",
        required_exact_lookups=("ITA 165", "ITA 166.1", "ITA 169", "ITA 167"),
        required_cra_sources=("CRA objections guidance", "T400A", "P148"),
        required_forms=("Notice of objection", "Tax Court filing documents if appealed"),
        conditional_checks=(
            "Deadline calculator based on assessment date and taxpayer type",
            "Extension request if objection deadline missed",
            "Tax Court appeal deadline if objection decision issued",
        ),
        missing_fact_questions=(
            "What is the date on the notice of assessment or reassessment?",
            "Is the taxpayer an individual, trust, or corporation?",
            "Has a notice of objection already been filed?",
            "Has CRA issued a confirmation, variation, or reassessment after objection?",
        ),
        human_review_triggers=(
            "Deadline may already have passed",
            "Large disputed amount or collection action",
            "Tax Court appeal deadline is near",
        ),
    ),
    WorkflowId.TRUST_T3_REPORTING: WorkflowContract(
        workflow_id=WorkflowId.TRUST_T3_REPORTING,
        label="Trust T3 and Schedule 15 reporting",
        required_exact_lookups=("ITA 104", "ITA 107", "ITA 108", "ITA 75(2)"),
        required_cra_sources=("T3 Trust Guide", "CRA trust filing guidance"),
        required_forms=("T3 return", "T3 slips", "T3 Schedule 15"),
        conditional_checks=(
            "Bare trust administrative position for the relevant taxation year",
            "21-year deemed disposition",
            "Non-resident beneficiary or trust residence issue",
            "Trust deed and trustee resolution constraints",
        ),
        missing_fact_questions=(
            "What type of trust is it and what taxation year is involved?",
            "What do the trust deed and resolutions say?",
            "Were amounts legally payable to beneficiaries before year-end?",
            "Is the trust a bare trust, personal trust, GRE, or non-resident trust?",
        ),
        human_review_triggers=(
            "Bare trust uncertainty",
            "Trust nearing 21-year anniversary",
            "Non-resident trustees, contributors, or beneficiaries",
        ),
    ),
}
