# Legal RAG Retrieval Diagnostics Gate

`GET /api/v1/maintenance/legal-rag-retrieval-diagnostics-gate`

Related local-observation endpoint:

`POST /api/v1/maintenance/legal-rag-retrieval-observation-gate`

This maintenance endpoint returns metadata-only release evidence for Legal RAG
retrieval diagnostics. It records deterministic diagnostic rows for local
reviewers so retrieval quality problems are visible before answer release.

## Diagnostic Dimensions

The gate is focused on retrieval metadata, not generated legal answers:

- Query intent: labels the type of legal research request being checked, such
  as primary authority lookup, local rule review, cross-jurisdiction drift, or
  missing index coverage.
- Authority coverage: compares expected source coverage with selected source
  counts and links weak coverage to authority/citation review rows.
- Top-k depth: flags empty or shallow retrieval depth before answer generation
  can rely on the result set.
- Jurisdiction and freshness: checks whether retrieval metadata matches the
  intended jurisdiction and whether source freshness is fresh, review-due,
  stale, or unknown.
- Citation and retrieval gap: distinguishes citation-map mismatches from
  retrieval coverage gaps, and blocks release when both overlap or when index
  coverage is empty.

## Linkage

The retrieval diagnostics gate is a join layer over existing local metadata:

- `legal-rag-index-binding`: provides the metadata-only retrieval-plan contract
  and selected-source linkage. The diagnostics gate does not rebuild or query
  the index.
- `legal-rag-authority-citation-gate`: supplies authority tier, jurisdiction,
  freshness, citation mismatch, and retrieval-gap rows used for reviewer
  linkage.
- `legal-rag-abstention-escalation-gate`: maps retrieval outcomes to answer,
  warning, clarification, lawyer-review, abstention, or premium-exception
  boundaries.
- `model-escalation-policy`: supplies cheap-first and premium-exception labels
  only. The diagnostics endpoint does not select or call a model.
- `legal-rag-embedding-retrieval-diagnostics-handoff-gate`: supplies
  metadata-only ready/hold/block handoff rows from post-commit index
  verification. These handoff rows are references for diagnostics review only;
  they do not enable production retrieval or include query text, retrieved
  context, source ids, source chunks, vectors, committer identity, or
  credentials.

## Cheap-First And Premium Exception Boundary

Cheap-first metadata review is the default. Ready rows can allow retrieval use,
partial or stale rows require reviewer review, and empty coverage blocks Legal
RAG answer release.

Premium exception is not a shortcut around retrieval defects. It is allowed
only as an explicit operator-reviewed boundary after cheap-first metadata checks
show that a premium path is appropriate. It still cannot bypass missing index
coverage, shallow top-k depth, jurisdiction mismatch, stale or unknown law,
missing citations, retrieval gaps, abstention, or lawyer-review blockers.

## Metadata Boundary

The gate may return only metadata such as:

- row ids and query-intent labels;
- selected and expected source counts;
- top-k depth and status labels;
- jurisdiction and freshness status labels;
- citation-gap and retrieval-gap booleans;
- linked gate ids and linked authority row ids;
- cheap-first action labels, release actions, reason codes, and validation
  commands.

It must not call NewAPI, Gemini, OpenAI, models, gateways, crawlers, or the
network. It must not download datasets. It must not save or return raw query,
raw retrieved context, raw legal text, prompts, model outputs, gateway payloads,
credentials, account data, client material, or emails.

## Release Integration

This is optional release evidence linked to:

- `legal-rag-retrieval-diagnostics-gate`
- `legal-rag-index-binding`
- `legal-rag-authority-citation-gate`
- `legal-rag-abstention-escalation-gate`
- `model-escalation-policy`
- `frontend-ui-regression-gate`

It supports release readiness, the continuous update ledger, OSS maintenance
evidence, and maintenance UI regression coverage. It does not prove live Legal
RAG accuracy, public benchmark scores, live gateway quality, broad jurisdiction
coverage, or automatic client delivery.

Use `LEGAL_RAG_RETRIEVAL_OBSERVATION_GATE.md` when a maintainer wants to paste
sanitized local retrieval observation metadata and get ready/review/blocked
release actions without returning source ids, raw queries, retrieved context,
or legal text.

## Validation

```bash
cd app/backend
python -m pytest tests/test_legal_rag_retrieval_diagnostics_gate.py tests/test_legal_rag_index_binding.py tests/test_legal_rag_evaluation.py -q
python -m pytest tests/test_legal_rag_retrieval_diagnostics_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
```
