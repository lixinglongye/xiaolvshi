# Feedback User-Need Legal-Document Benchmark Backlog

This maintenance slice connects privacy-safe feedback clusters to roadmap user
needs and legal-document benchmark evidence.

## Endpoint

- `GET /api/v1/maintenance/feedback/user-need-legal-document-benchmark-backlog`
- `POST /api/v1/maintenance/feedback/user-need-legal-document-benchmark-backlog`

The POST body accepts an `items` array of feedback metadata. The service uses
deterministic local clustering, user-need roadmap alignment, user-need legal
document benchmark evidence, and document coverage metadata to rank backlog
rows for fixture creation or review.

## What It Returns

- `backlog_rows`: normalized feedback cluster rows mapped to `user_need_ids`,
  benchmark case IDs, legal-document case IDs, document type suggestions,
  release gates, reason codes, priority scores, and next actions.
- `summary`: counts for processed feedback, clusters, mapped needs, fixture
  suggestions, blocked rows, review rows, and ready rows.
- `privacy_boundary`: explicit false flags for raw feedback, PII, document
  snippets, public benchmark text, prompts, model outputs, payload bodies, and
  credentials.
- `claim_boundary`: explicit false flags for feedback-resolution, public
  benchmark score, production quality, and client-document coverage claims.

## Safety

This is metadata-only maintenance evidence. It does not call models, gateways,
or the network. It does not store or return raw feedback, customer notes, PII,
uploaded legal documents, fixture snippets, public benchmark text, prompts,
payload bodies, gateway responses, model outputs, or credentials.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_feedback_user_need_legal_document_benchmark_backlog.py -q
python -m pytest tests/test_feedback_user_need_legal_document_benchmark_backlog.py tests/test_feedback_issue_cluster.py tests/test_feedback_roadmap_alignment.py tests/test_user_need_legal_document_benchmark_evidence.py tests/test_user_need_implementation_priority_queue.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/feedback_user_need_legal_document_benchmark_backlog.py`
- `app/backend/tests/test_feedback_user_need_legal_document_benchmark_backlog.py`
- `app/backend/services/feedback_issue_cluster.py`
- `app/backend/services/feedback_roadmap_alignment.py`
- `app/backend/services/user_need_legal_document_benchmark_evidence.py`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
