# Legal RAG Hallucination Triage Gate

`GET /api/v1/maintenance/legal-rag-hallucination-triage-gate`

This maintenance endpoint returns metadata-only Legal RAG hallucination triage evidence for release review. It maps local failure-fixture labels to severity, reviewer actions, release blockers, and related authority/citation gate rows.

## Scope

- Uses deterministic local fixture metadata and authority/citation gate metadata.
- Blocks client delivery by default for critical or high hallucination-risk rows.
- Links to release readiness, the continuous update ledger, OSS maintenance evidence, and the frontend UI regression protected panel.
- Does not claim hallucination-free legal answers, legal advice accuracy, public benchmark scores, live gateway quality, or automatic client delivery.

## Privacy Boundary

The gate is metadata-only. It does not call NewAPI, Gemini, model gateways, crawlers, or benchmark services. It does not download datasets and does not store or return raw legal text, retrieved snippets, prompts, model outputs, gateway payloads, credentials, or client material.

## Evidence Paths

- `app/backend/services/legal_rag_hallucination_triage_gate.py`
- `app/backend/tests/test_legal_rag_hallucination_triage_gate.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/maintenance_evidence.py`
- `app/backend/services/frontend_ui_regression_gate.py`
- `docs/LEGAL_RAG_HALLUCINATION_TRIAGE_GATE.md`

## Validation

```bash
python -m pytest tests/test_legal_rag_hallucination_triage_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
```
