# Legal Grounding Quick Audit

The legal grounding quick audit combines citation reviewability, evidence-plan completeness, and RAG grounding metrics into one deterministic release signal.

## Endpoints

```http
GET /api/v1/legal-knowledge/grounding-quick-audit-policy
POST /api/v1/legal-knowledge/grounding-quick-audit
```

`POST` accepts either a deep-review report directly or an object with `report` and optional `rag_run`:

```json
{
  "report": {
    "risk_items": [],
    "legal_authority_appendix": [],
    "professional_review_framework": {}
  },
  "rag_run": {
    "expected_source_ids": [],
    "retrieved_source_ids": [],
    "answer_citation_source_ids": [],
    "verified_claim_count": 0,
    "total_claim_count": 0,
    "unsupported_claims": [],
    "stale_source_ids": [],
    "pii_findings": []
  }
}
```

If `rag_run` is missing, the service infers conservative RAG metrics from the report's legal authority appendix and risk-item citations. Inferred metrics produce a warning so maintainers know to run explicit RAG evaluation before public release.

## What It Checks

- High-risk legal findings have reviewable citations.
- High-risk legal findings have concrete evidence plans.
- Cited source IDs are present in retrieved or appendix sources.
- Expected legal sources are retrieved.
- Unsupported high-impact legal claims block release.
- Stale sources and privacy findings are surfaced before evidence is archived.

## Research Basis

- LegalBench: multi-task legal reasoning coverage.
- RAGAS: faithfulness, answer relevance, and context/source relevance.
- CRAG: factual QA and retrieval-style grounding reliability.

## Validation

```bash
python -m pytest tests/test_legal_grounding_quick_audit.py tests/test_legal_rag_evaluation.py tests/test_citation_audit.py tests/test_evidence_audit.py -q
```

## Safety

The service does not call models, gateways, search engines, or public datasets. It evaluates structured report metadata, source IDs, citation links, and normalized RAG metrics only. Do not commit real client documents, raw model outputs, emails, API keys, or passwords.

## Related Files

- `app/backend/services/legal_grounding_quick_audit.py`
- `app/backend/tests/test_legal_grounding_quick_audit.py`
- `app/backend/services/legal_rag_evaluation.py`
- `app/backend/services/citation_audit.py`
- `app/backend/services/evidence_audit.py`
- `app/backend/routers/legal_knowledge.py`
- `docs/LEGAL_RAG_EVALUATION.md`
- `docs/DEEP_REVIEW_CITATION_AUDIT.md`
- `docs/DEEP_REVIEW_EVIDENCE_AUDIT.md`
