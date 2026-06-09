# Feedback User-Need Legal-Document Benchmark Release Packet

This maintenance slice gates privacy-safe feedback benchmark backlog rows before
they can enter customer-visible resolution review.

## Endpoint

- `GET /api/v1/maintenance/feedback/user-need-legal-document-benchmark-release-packet`
- `POST /api/v1/maintenance/feedback/user-need-legal-document-benchmark-release-packet`

The POST body accepts feedback `items`, optional `legal_document_evidence`, and
optional `release_observations`. Observations are status metadata only, such as
release validation status, implementation review status, gate IDs, and whether a
privacy-safe resolution note exists.

## What It Returns

- `release_rows`: feedback cluster rows joined to user needs, benchmark action
  status, legal-document evidence status, implementation queue status,
  lifecycle blockers, release gate IDs, reason codes, and next actions.
- `summary`: counts for ready, review, blocked, and high-risk blocked rows.
- `privacy_boundary`: explicit false flags for raw feedback, customer notes,
  public resolution text, PII, document snippets, fixture snippets, prompt text,
  payload bodies, model output, and credentials.
- `claim_boundary`: explicit false flags for feedback resolution, customer
  notification, production quality, public benchmark scores, and client-document
  coverage.

## Safety

This is metadata-only release review evidence. It does not call models,
gateways, or the network. It does not store or return raw feedback, customer
notes, public resolution text, PII, uploaded legal documents, fixture snippets,
public benchmark text, prompts, payload bodies, gateway responses, model
outputs, or credentials.

Ready rows mean the metadata is ready for maintainer approval. They do not prove
customer notification, production legal quality, public benchmark performance,
or real client-document coverage.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_feedback_user_need_legal_document_benchmark_release_packet.py -q
python -m pytest tests/test_feedback_user_need_legal_document_benchmark_release_packet.py tests/test_feedback_user_need_legal_document_benchmark_backlog.py tests/test_feedback_lifecycle_policy.py tests/test_user_need_implementation_priority_queue.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/feedback_user_need_legal_document_benchmark_release_packet.py`
- `app/backend/tests/test_feedback_user_need_legal_document_benchmark_release_packet.py`
- `app/backend/services/feedback_user_need_legal_document_benchmark_backlog.py`
- `app/backend/services/feedback_lifecycle_policy.py`
- `app/backend/services/user_need_implementation_priority_queue.py`
- `app/backend/services/user_need_legal_document_benchmark_evidence.py`
- `app/backend/routers/maintenance.py`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
