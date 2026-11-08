# Curriculum data and sourcing

The current `curriculum.csv`, `learning_materials.csv`, and `graph_nodes.csv`
are prototype data. The first two files now mark their records
`prototype_unverified`; they have no country or source attribution and must not
be presented as official Ugandan or East African curriculum content.

## Uganda-first intake

Use `uganda_primary_math_outcomes.csv` to record concise, reviewed paraphrases
of official Uganda Primary 1-7 mathematics outcomes. Required provenance for
each outcome:

- Country code (`UG`), curriculum name, version or publication year, grade and
  term (when available).
- Strand/sub-strand and outcome wording, with a stable outcome ID.
- Source title, official URL, page/section, and reuse license or permission
  status.
- Review status. Use `reviewed` only after both source accuracy and permission
  to store/reuse the content are confirmed.

The NCDC website links to its resources portal and e-library. The public pages
reviewed so far did not provide an accessible primary mathematics outcome
dataset, and the e-library asks visitors to register. Obtain the current
curriculum document from NCDC or its library and confirm reuse rights before
transcribing or importing content. Official publication does not automatically
mean unrestricted reuse. The e-library page lists `irene.nakayenga@ncdc.go.ug`
and `luke.bukenya@ncdc.go.ug` for library enquiries.

Two locally supplied NCDC documents have been reviewed:

- `P4_MATHEMATICS_SYLLABUS-1.pdf` is the Uganda Mathematics Syllabus for
  Primary Four, published by NCDC in 2010 (ISBN 978-9970-117-40-6). It is a
  direct curriculum source, but its copyright page explicitly prohibits
  reproducing, storing, or transmitting any part without permission. Treat it
  as a reference for manual review only until permission is obtained. It is
  also an older syllabus and should not be assumed current.
- `P5_Merged.pdf` is NCDC Home-Study Learning Primary Five, published in 2020
  for COVID-19 school closures. It contains a Mathematics section, so it may
  inform Primary Five lesson examples, but it is an intervention resource,
  not a current curriculum specification. Its notice restricts reproduction
  for commercial gains; other reuse rights are unclear. Confirm permission
  before copying its content into G-RAFT, the CSV files, or Qdrant.

Both documents are registered in `curriculum_sources.csv`. Their local
availability does not establish permission to redistribute, transform, or
store their text in an application.

The user has also supplied the 2012 `PRIMARY-SEVEN-SET-ONE.pdf` and explicitly
authorized its use in this project. It is an NCDC Uganda Primary Seven
curriculum document; its Mathematics Syllabus occupies PDF pages 148-189
(printed pages 127-168). The publisher notice still states permission is
required for reproduction. The user's authorization is recorded as project
permission, not as an open license or permission for redistribution. Source
facts added to internal evaluation data should use pinpoint page references.

## East African comparisons

`eac_curriculum_alignments.csv` is deliberately a separate crosswalk. Record
the source and target country, curriculum version, grade, outcome IDs, evidence,
and reviewer decision for each proposed alignment. Do not assume that same
grade numbers or similar topic names mean identical learning outcomes. Use
`proposed` until evidence has been reviewed; only then set an alignment to
`reviewed`.

The East African Community's education page describes harmonisation as
comparison and alignment of national systems. It is not a single regional
primary mathematics syllabus. Country curriculum sources are listed in
`curriculum_sources.csv`; confirm the current document and the reuse terms for
each one before adding its content.

## Adding learning materials

`learning_materials.csv` supports the existing retrieval service and includes
optional provenance columns. For new source-grounded entries, use a unique
integer `id`, `country_code`, curriculum/version, source title and URL, page or
section, license, and `source_status=reviewed` only after content and reuse
rights have both been checked. A material without verified attribution
defaults to `prototype_unverified` and is excluded from a country-specific
Qdrant search.

Run `POST /vector/load-materials` after updating the CSV to refresh the Qdrant
collection. Country-scoped tutor requests use the `country_code` field. The
legacy graph loader is not yet curriculum-scoped; country-scoped requests
therefore do not use its graph context until that graph data model is updated.

## Initial hallucination-evaluation set

`evaluation_cases.csv` is the first small, traceable evaluation set. It keeps
four kinds of cases separate:

- `automated_solver`: authored explicit arithmetic questions with expected
  results reproducible by the deterministic arithmetic service.
- `policy_only`: out-of-source and ambiguous questions with the desired
  abstain/clarify behavior. These are not automated because the live tutor
  does not implement a checked abstention policy yet.
- `blocked_pending_source`: curriculum questions that cannot be scored until an
  approved, reusable curriculum source is added and reviewed.
- `manually_verified_source_fact`: concise document-specific facts from the
  user-authorized P7 2012 PDF, manually checked against a pinpoint page. These
  describe that edition only; they must not be presented as current curriculum
  without newer evidence.

Run `python -m pytest -q tests/test_evaluation_dataset.py` from the repository
root to validate the dataset and arithmetic ground truth. Do not combine these
categories into one accuracy score: arithmetic solver correctness, evidence
coverage, and abstention behavior need separate measures. This starter set
validates test data and deterministic arithmetic, with one manually checked P7
fact. It does not yet execute the tutor against curriculum facts, measure LLM
hallucinations, or demonstrate that graph retrieval improves answers.

To evaluate the live tutor against the manually checked fact list, start the
backend and its configured services, then run
`python -m backend.evaluation_service` from the repository root. The evaluator
submits each `manually_verified_source_fact` case to `/tutor/ask` and reports
expected-item coverage, missing items, citation-reference status, and retrieved
source titles. Coverage only measures whether expected list items appear in
the answer; it does not detect unsupported extra claims or prove that retrieved
sources support the answer. Keep this score separate from arithmetic and
citation-reference checks. The current P7 case describes the supplied 2012
document only.

## Inspecting runtime retrieval

`POST /tutor/ask` responses include `retrieval_trace`. It records the vector
search filters, threshold, hit count, material IDs, relevance scores, and source
metadata for each returned passage. `retrieved_materials` retains the full
passage text. The trace also records whether the graph lookup was performed,
skipped, or found no node, along with the queried topic and node ID.

Graph nodes currently have no source provenance stored, so a graph hit is
explicitly marked `provenance_status=not_recorded`. A trace makes retrieval
observable; it does not prove that the generated response is supported by
those sources. The Streamlit source expander displays this trace when
"Show retrieved curriculum information" is enabled.

## Live verification status

The live tutor response includes a `verification` result. The arithmetic
branch checks the deterministic answer against the question and reports
`passed` or `failed`. For non-arithmetic answers, the tutor cites retrieved
evidence IDs and checks that citations refer to available evidence and that
each response sentence includes a citation. One correction attempt is made
when this citation check fails; if the correction still fails, the tutor
abstains instead of displaying the unchecked draft. Passing the citation check
does **not** show that the cited evidence supports the claims; semantic
correctness remains `not_checked`. If no evidence is retrieved, the tutor
abstains instead of generating an unsupported curriculum answer.
