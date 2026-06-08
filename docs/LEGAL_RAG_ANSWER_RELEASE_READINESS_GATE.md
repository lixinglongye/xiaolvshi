# Legal RAG Answer Release Readiness Gate

`legal-rag-answer-release-readiness-gate` adds a metadata-only gate after
retrieval observation review and before any Legal RAG answer is treated as
release-ready.

## Endpoint

- `GET /api/v1/maintenance/legal-rag-answer-release-readiness-gate`
- `POST /api/v1/maintenance/legal-rag-answer-release-readiness-gate`

The POST body may provide sanitized retrieval observations, an existing
`retrieval_observation_gate`, or direct `observation_rows`. Direct observation
rows are used as metadata rows and are not expanded into raw query, context, or
source material.

## What It Provides

- Ready, review-required, and blocked answer-release rows.
- Internal answer draft actions for ready rows.
- Citation packet requirements and lawyer-review requirements.
- Cheap-first continue, verify, and escalation boundaries.
- Client-delivery false flags and legal-advice claim boundaries.

## Release Rules

A row is ready only when retrieval observation metadata is ready, the retrieval
release action allows retrieval use, source coverage is ready, top-k depth is
sufficient, jurisdiction is matched, and source freshness is fresh.

Review-required rows must go to lawyer or maintainer review before answer
release. Blocked rows block answer release entirely until retrieval blockers are
resolved.

Ready rows may prepare internal answer drafts with citation packets. They do not
enable automatic client delivery or prove legal answer quality.

## Boundaries

This gate does not write an answer, send client delivery, claim legal advice,
claim answer quality, query an index, call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, models, crawlers, or the network. It does not
download datasets, change defaults, shift traffic, or persist client material.

It also does not return source ids, raw query text, user questions, retrieved
context, raw legal text, source chunks, prompts, model outputs, gateway payloads,
credentials, emails, account data, legal advice, or client delivery material.

## Validation

```bash
cd app/backend
python -m pytest tests/test_legal_rag_answer_release_readiness_gate.py tests/test_legal_rag_retrieval_observation_gate.py -q
python -m pytest tests/test_legal_rag_answer_release_readiness_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```
