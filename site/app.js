const workflows = [
  {
    id: "interest_deductibility",
    label: "Interest deductibility",
    fullLabel: "Interest deductibility",
    description: "Tracing, source, financing, withholding.",
    samplePrompt: "Our corporation borrowed to refinance shareholder advances and pay a dividend. Can we deduct the interest?",
    law: ["ITA 20(1)(c)", "ITA 18(1)(a)", "ITA 18(1)(b)", "ITA 67"],
    cra: ["CRA Folio S3-F6-C1"],
    forms: ["T106 if non-arm's length non-resident interest", "NR4 if Part XIII reporting applies"],
    cases: ["Shell", "Ludco", "Singleton"],
    conditional: [
      "Thin capitalization / EIFEL if cross-border or group financing",
      "Part XIII withholding and treaty rate if non-resident lender",
      "Transfer pricing documentation if non-arm's length cross-border debt"
    ],
    missingFacts: [
      "What was the direct current use of the borrowed money?",
      "Who is the lender and are the parties related or non-resident?",
      "Is there a legal obligation to pay interest?",
      "What taxation year applies?"
    ],
    review: [
      "Circular cash movements",
      "Related-party cross-border financing",
      "Aggressive surplus extraction or loss consolidation"
    ]
  },
  {
    id: "section_85_rollover",
    label: "Subsection 85 rollover",
    fullLabel: "Subsection 85 rollover",
    description: "Eligibility, elected amount, forms, deadlines.",
    samplePrompt: "I want to transfer appreciated Opco shares to a new Holdco for shares and a note. What must we file and what can go wrong?",
    law: ["ITA 85(1)", "ITA 85(6)", "ITA 85(7)", "ITA 85(7.1)"],
    cra: ["IC76-19R3"],
    forms: ["T2057", "T2058 if partnership transfer"],
    cases: [],
    conditional: [
      "ITA 84.1 if private corporation shares move to non-arm's length corporation",
      "ITA 55 if intercorporate dividends are part of the series",
      "ETA 167 if business assets are transferred",
      "Land transfer tax if real property is transferred"
    ],
    missingFacts: [
      "Who are the transferor and transferee?",
      "Is the transferee a taxable Canadian corporation?",
      "What property is being transferred and what are FMV, ACB, UCC, liabilities, and elected amount?",
      "What are the filing due dates for all parties?"
    ],
    review: [
      "Private corporation share transfer to related corporation",
      "Valuation uncertainty",
      "Series involving dividends, redemptions, or sale to children/holdco"
    ]
  },
  {
    id: "shareholder_benefit",
    label: "Shareholder benefit",
    fullLabel: "Shareholder benefit",
    description: "Capacity, valuation, reporting exposure.",
    samplePrompt: "The corporation paid for renovations to a shareholder's home and booked it to the shareholder account. Is that taxable?",
    law: ["ITA 15(1)", "ITA 15(2)", "ITA 80.4", "ITA 6", "ITA 69", "ITA 246"],
    cra: ["CRA Folio S3-F1-C1", "CRA Folio S3-F1-C2"],
    forms: ["T4/T4A/T5 depending on characterization"],
    cases: [],
    conditional: [
      "Payroll remittances if employment compensation",
      "GST/HST consequences for personal use of corporate property",
      "Audit manual Chapter 24 as audit practice only"
    ],
    missingFacts: [
      "What benefit was provided and to whom?",
      "Was the person acting as shareholder, employee, or both?",
      "Was there a written loan, lease, reimbursement, or shareholder account entry?",
      "What is the fair market value?"
    ],
    review: [
      "Weak valuation",
      "Large personal expenses in corporate books",
      "Year-end journal entries without legal support"
    ]
  },
  {
    id: "shareholder_loan",
    label: "Shareholder loan",
    fullLabel: "Shareholder loan",
    description: "Loan inclusion, benefit, repayment timing.",
    samplePrompt: "A shareholder took advances from the company and repaid them after year-end. Can we avoid a taxable benefit?",
    law: ["ITA 15(2)", "ITA 80.4", "ITA 20(1)(j)"],
    cra: ["CRA Folio S3-F1-C1", "CRA Folio S3-F1-C2"],
    forms: ["T2 shareholder account support", "T5/T4A if recharacterized"],
    cases: [],
    conditional: [
      "Repayment within statutory period",
      "Series of loans and repayments",
      "Prescribed-rate benefit calculation",
      "Payroll or dividend reporting if loan characterization fails"
    ],
    missingFacts: [
      "Who received the loan and what is their shareholder/related status?",
      "When was the loan advanced and repaid, if repaid?",
      "Was there a written loan agreement and interest charged?",
      "Is there a series of advances and repayments?"
    ],
    review: [
      "Repeated year-end repayments and readvances",
      "No debtor-creditor documentation",
      "Large debit shareholder loan account"
    ]
  },
  {
    id: "employee_vs_contractor",
    label: "Employee vs contractor",
    fullLabel: "Employee vs contractor",
    description: "Status, payroll, CPP/EI, GST/HST.",
    samplePrompt: "We pay a full-time consultant through invoices, but we set hours and provide equipment. Contractor or employee?",
    law: ["ITA 5", "ITA 6", "ITA 8", "ITA 9", "ITA 153", "ITR 100", "ITR 102"],
    cra: ["CRA employment status guidance", "T4001"],
    forms: ["TD1", "T4", "T4A", "CPT1 if CPP/EI ruling requested"],
    cases: ["Sagaz", "Wiebe Door"],
    conditional: [
      "CPP/EI pensionable and insurable employment",
      "GST/HST registration if genuinely self-employed",
      "Quebec payroll/social contribution rules if Quebec involved"
    ],
    missingFacts: [
      "Who controls hours, tools, work location, substitution, and deliverables?",
      "Can the worker profit or suffer loss?",
      "Does actual conduct match the written contract?",
      "What province is involved?"
    ],
    review: ["Mixed facts with significant retroactive payroll exposure"]
  },
  {
    id: "section_116_tcp",
    label: "Section 116 disposition",
    fullLabel: "Non-resident disposition of taxable Canadian property",
    description: "TCP status, certificates, withholding, treaty.",
    samplePrompt: "A non-resident is selling shares of a Canadian private company that owns real estate. What does the buyer need to withhold?",
    law: ["ITA 2(3)", "ITA 115", "ITA 116", "ITA 248(1)", "ITA 54"],
    cra: ["IC72-17R6", "T4058"],
    forms: ["T2062 series"],
    cases: ["Alta Energy if treaty/GAAR issue is present"],
    conditional: [
      "Treaty text, protocols, and MLI status",
      "Purchaser withholding liability",
      "GST/HST, UHT, and provincial land transfer taxes for real property"
    ],
    missingFacts: [
      "What is the vendor's residence and treaty country?",
      "What property is being sold?",
      "Was a certificate obtained before closing?",
      "Do shares derive value principally from Canadian real/resource/timber property?"
    ],
    review: [
      "Treaty-protected property claim",
      "Private company shares with Canadian real property value",
      "Closing occurred without certificate"
    ]
  },
  {
    id: "principal_residence",
    label: "Principal residence exemption",
    fullLabel: "Principal residence exemption",
    description: "Designation years, change in use, T2091.",
    samplePrompt: "We sold a home that was rented for two years and lived in for six. Can we claim the principal residence exemption?",
    law: ["ITA 40(2)(b)", "ITA 54", "ITA 45"],
    cra: ["CRA Folio S1-F3-C2"],
    forms: ["T2091", "Schedule 3"],
    cases: [],
    conditional: [
      "Change-in-use election if rental/business use occurred",
      "Property flipping deeming rule if short holding period",
      "GST/HST if new/substantially renovated or business property",
      "Provincial real estate and vacancy/speculation tax issues"
    ],
    missingFacts: [
      "Which years was the property ordinarily inhabited?",
      "Was any part rented or used for business?",
      "Was there a change in use?",
      "Were any other properties designated for the same years?"
    ],
    review: [
      "Mixed personal/rental/business use",
      "Multiple properties across the same years",
      "Sale shortly after acquisition"
    ]
  },
  {
    id: "t1135_foreign_reporting",
    label: "T1135 foreign reporting",
    fullLabel: "T1135 foreign reporting",
    description: "Foreign property, thresholds, penalties.",
    samplePrompt: "A client held US brokerage assets over CAD 100,000 and missed T1135 filings for three years. What now?",
    law: ["ITA 233.3", "ITA 162(7)", "ITA 162(10)"],
    cra: ["CRA T1135 guidance"],
    forms: ["T1135"],
    cases: [],
    conditional: [
      "Voluntary disclosures if missed filings exist",
      "Specified foreign property cost amount threshold",
      "Foreign affiliate reporting if T1134 may also apply"
    ],
    missingFacts: [
      "What specified foreign property was held and what was the cost amount?",
      "Was the total cost amount over CAD 100,000 at any time in the year?",
      "Were any prior-year T1135 forms missed?",
      "Are any assets held through a corporation, trust, or partnership?"
    ],
    review: [
      "Multiple missed years",
      "Potential gross negligence penalty",
      "Foreign affiliate or trust structure involved"
    ]
  },
  {
    id: "objections_appeals",
    label: "Objections and appeals",
    fullLabel: "Objections and appeals",
    description: "Assessment dates, deadlines, extensions.",
    samplePrompt: "CRA reassessed a 2023 T2 six months ago. Can we still object, and what deadline matters?",
    law: ["ITA 165", "ITA 166.1", "ITA 169", "ITA 167"],
    cra: ["CRA objections guidance", "T400A", "P148"],
    forms: ["Notice of objection", "Tax Court filing documents if appealed"],
    cases: [],
    conditional: [
      "Deadline calculator based on assessment date and taxpayer type",
      "Extension request if objection deadline missed",
      "Tax Court appeal deadline if objection decision issued"
    ],
    missingFacts: [
      "What is the date on the notice of assessment or reassessment?",
      "Is the taxpayer an individual, trust, or corporation?",
      "Has a notice of objection already been filed?",
      "Has CRA issued a confirmation, variation, or reassessment after objection?"
    ],
    review: [
      "Deadline may already have passed",
      "Large disputed amount or collection action",
      "Tax Court appeal deadline is near"
    ]
  },
  {
    id: "trust_t3_reporting",
    label: "Trust T3 and Schedule 15",
    fullLabel: "Trust T3 and Schedule 15 reporting",
    description: "Trust type, payable income, ownership.",
    samplePrompt: "A family trust distributed dividends and capital gains to beneficiaries. What T3 and Schedule 15 reporting do we need?",
    law: ["ITA 104", "ITA 107", "ITA 108", "ITA 75(2)"],
    cra: ["T3 Trust Guide", "CRA trust filing guidance"],
    forms: ["T3 return", "T3 slips", "T3 Schedule 15"],
    cases: [],
    conditional: [
      "Bare trust administrative position for the relevant taxation year",
      "21-year deemed disposition",
      "Non-resident beneficiary or trust residence issue",
      "Trust deed and trustee resolution constraints"
    ],
    missingFacts: [
      "What type of trust is it and what taxation year is involved?",
      "What do the trust deed and resolutions say?",
      "Were amounts legally payable to beneficiaries before year-end?",
      "Is the trust a bare trust, personal trust, GRE, or non-resident trust?"
    ],
    review: [
      "Bare trust uncertainty",
      "Trust nearing 21-year anniversary",
      "Non-resident trustees, contributors, or beneficiaries"
    ]
  }
];

const answerSections = [
  "Issue classification",
  "Short answer with confidence",
  "Authority-ranked law and regulations",
  "CRA administrative position",
  "Forms, elections, and deadlines",
  "Cases and hierarchy notes",
  "Missing facts",
  "Risk flags and human-review trigger"
];

let activeWorkflow = workflows[0];

const workflowList = document.querySelector("#workflowList");
const workflowSearch = document.querySelector("#workflowSearch");
const workflowTitle = document.querySelector("#workflowTitle");
const sourceCount = document.querySelector("#sourceCount");
const factCount = document.querySelector("#factCount");
const reviewCount = document.querySelector("#reviewCount");
const samplePrompt = document.querySelector("#samplePrompt");
const runWorkflow = document.querySelector("#runWorkflow");
const traceList = document.querySelector("#traceList");
const confidenceChip = document.querySelector("#confidenceChip");
const answerBackboneElement = document.querySelector("#answerBackbone");
const agentAnswer = document.querySelector("#agentAnswer");
const agentStatus = document.querySelector("#agentStatus");
const useOllama = document.querySelector("#useOllama");
const ollamaEndpoint = document.querySelector("#ollamaEndpoint");
const ollamaModel = document.querySelector("#ollamaModel");

const lists = {
  law: document.querySelector("#lawList"),
  cra: document.querySelector("#craList"),
  forms: document.querySelector("#formList"),
  cases: document.querySelector("#caseList"),
  conditional: document.querySelector("#conditionalList"),
  missingFacts: document.querySelector("#missingFactsList"),
  review: document.querySelector("#reviewList")
};

function renderWorkflowList(filter = "") {
  const normalized = filter.trim().toLowerCase();
  workflowList.innerHTML = "";

  workflows
    .filter((workflow) => {
      const haystack = `${workflow.label} ${workflow.fullLabel || ""} ${workflow.description} ${workflow.id}`.toLowerCase();
      return haystack.includes(normalized);
    })
    .forEach((workflow) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `workflow-button ${workflow.id === activeWorkflow.id ? "active" : ""}`;
      button.innerHTML = `<strong>${workflow.label}</strong><span>${workflow.description}</span>`;
      button.addEventListener("click", () => {
        activeWorkflow = workflow;
        render();
      });
      workflowList.append(button);
    });
}

function renderList(element, items, emptyText = "No mandatory source in this contract") {
  element.innerHTML = "";
  const values = items.length ? items : [emptyText];
  values.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    element.append(li);
  });
}

function buildTrace(workflow) {
  return [
    `Classify prompt as ${workflow.label}.`,
    `Run exact lookups for ${workflow.law.length} law and regulation targets.`,
    `Retrieve CRA position without treating it as binding law.`,
    `Check ${workflow.forms.length} form, filing, or deadline targets.`,
    `Evaluate ${workflow.missingFacts.length} missing fact questions before confidence.`,
    `Apply ${workflow.review.length} human-review trigger checks.`
  ];
}

function renderTrace(workflow) {
  traceList.innerHTML = "";
  buildTrace(workflow).forEach((step) => {
    const li = document.createElement("li");
    li.textContent = step;
    traceList.append(li);
  });
  confidenceChip.textContent = workflow.review.length > 2 ? "Review likely" : "Triage";
  confidenceChip.className = workflow.review.length > 2 ? "chip chip-warn" : "chip";
}

function renderTraceItems(items) {
  traceList.innerHTML = "";
  items.forEach((step) => {
    const li = document.createElement("li");
    li.textContent = step;
    traceList.append(li);
  });
}

function renderBackbone() {
  answerBackboneElement.innerHTML = "";
  answerSections.forEach((section) => {
    const div = document.createElement("div");
    div.textContent = section;
    answerBackboneElement.append(div);
  });
}

function render() {
  workflowTitle.textContent = activeWorkflow.fullLabel || activeWorkflow.label;
  samplePrompt.value = activeWorkflow.samplePrompt;
  sourceCount.textContent = activeWorkflow.law.length + activeWorkflow.cra.length + activeWorkflow.forms.length + activeWorkflow.cases.length;
  factCount.textContent = activeWorkflow.missingFacts.length;
  reviewCount.textContent = activeWorkflow.review.length;

  renderWorkflowList(workflowSearch.value);
  renderList(lists.law, activeWorkflow.law);
  renderList(lists.cra, activeWorkflow.cra);
  renderList(lists.forms, activeWorkflow.forms);
  renderList(lists.cases, activeWorkflow.cases);
  renderList(lists.conditional, activeWorkflow.conditional);
  renderList(lists.missingFacts, activeWorkflow.missingFacts);
  renderList(lists.review, activeWorkflow.review);
  renderTrace(activeWorkflow);
  renderBackbone();
  agentAnswer.textContent = "Enter a question and run the live agent. The backend will classify the workflow, assemble the required source checklist, and optionally call Ollama for a cautious draft.";
  agentStatus.textContent = "Ready";
  agentStatus.className = "chip chip-neutral";
}

workflowSearch.addEventListener("input", () => renderWorkflowList(workflowSearch.value));
runWorkflow.addEventListener("click", async () => {
  const text = samplePrompt.value.trim();
  if (!text) {
    agentAnswer.textContent = "Question text is required.";
    return;
  }

  agentStatus.textContent = "Running";
  agentStatus.className = "chip chip-warn";
  runWorkflow.disabled = true;

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        use_ollama: useOllama.checked,
        ollama_base_url: ollamaEndpoint.value,
        ollama_model: ollamaModel.value
      })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Agent request failed");
    }

    const matched = workflows.find((workflow) => workflow.id === data.workflow_id);
    if (matched) {
      activeWorkflow = matched;
      renderWorkflowList(workflowSearch.value);
      workflowTitle.textContent = activeWorkflow.fullLabel || activeWorkflow.label;
      sourceCount.textContent = activeWorkflow.law.length + activeWorkflow.cra.length + activeWorkflow.forms.length + activeWorkflow.cases.length;
      factCount.textContent = activeWorkflow.missingFacts.length;
      reviewCount.textContent = activeWorkflow.review.length;
      renderList(lists.law, activeWorkflow.law);
      renderList(lists.cra, activeWorkflow.cra);
      renderList(lists.forms, activeWorkflow.forms);
      renderList(lists.cases, activeWorkflow.cases);
      renderList(lists.conditional, activeWorkflow.conditional);
      renderList(lists.missingFacts, activeWorkflow.missingFacts);
      renderList(lists.review, activeWorkflow.review);
    }

    renderTraceItems(data.trace || []);
    agentAnswer.textContent = data.answer || "No answer returned.";
    agentStatus.textContent = useOllama.checked ? data.ollama_status : "Deterministic";
    agentStatus.className = data.status === "ok" ? "chip" : "chip chip-warn";
  } catch (error) {
    agentStatus.textContent = "Error";
    agentStatus.className = "chip chip-danger";
    agentAnswer.textContent = String(error.message || error);
  } finally {
    runWorkflow.disabled = false;
  }
});

render();
