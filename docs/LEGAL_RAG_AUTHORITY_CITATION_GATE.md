# Legal RAG Authority Citation Gate

This gate records metadata-only release evidence for Legal RAG authority and
citation quality.

## Endpoint

```http
GET /api/v1/maintenance/legal-rag-authority-citation-gate
```

The response includes authority rules, citation rules, source review rows,
citation mismatch rows, retrieval gap rows, required metadata fields, release
gate links, evidence paths, validation commands, an explicit claim boundary, and
an explicit privacy boundary.

## What It Checks

- Primary or official legal authority metadata is preferred before secondary or
  unknown source metadata.
- Jurisdiction, publication or effective date, freshness status, and validation
  status are required before a source can support deliverable legal output.
- Citation source ids must match selected source ids or retrieval-plan metadata.
- Missing, stale, unmatched, or incomplete citation metadata blocks delivery.
- Unknown authority tiers require lawyer or maintainer review.
- The maintenance UI can show source tier, authority level, jurisdiction,
  freshness, citation mismatch, and retrieval-gap counts without exposing source
  snippets.

## Metadata Boundary

The gate may use only metadata such as:

- `source_id`
- `source_type`
- `authority_tier`
- `jurisdiction`
- `publication_or_effective_date`
- `retrieval_plan_id`
- `selected_source_ids`
- `citation_map_source_ids`
- `freshness_status`
- `validation_status`

It must not call NewAPI, Gemini, model gateways, crawlers, or external dataset
downloaders. It must not save raw legal text, prompts, model output, gateway
payloads, credentials, account data, client material, or emails.

## Release Integration

This is optional release evidence linked to:

- `legal-rag-selected-source-request-metadata`
- `legal-rag-selected-source-citation-validation`
- `legal-rag-index-binding`
- `legal-source-freshness-policy`
- `deep-review-selected-source-binding`
- `case-export-readiness`
- `frontend-ui-regression-gate`

It supports reviewer visibility for the maintenance evidence page and frontend
regression protected panel list. It does not prove live Legal RAG accuracy,
public benchmark performance, broad jurisdiction coverage, or external legal
dataset validation.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_legal_rag_authority_citation_gate.py -q
python -m pytest tests/test_legal_rag_authority_citation_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
```
