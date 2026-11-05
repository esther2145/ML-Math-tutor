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
