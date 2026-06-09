# User Need Legal-Document Benchmark Evidence

`user_need_legal_document_benchmark_evidence.py` maps roadmap user needs to
local legal-document benchmark evidence.

## Endpoint

```http
GET /api/v1/maintenance/user-needs/legal-document-benchmark-evidence
POST /api/v1/maintenance/user-needs/legal-document-benchmark-evidence
```

## Purpose

The user-needs radar tells maintainers which product gaps matter most. The
legal-document benchmark suite, fact consistency checks, local rule baseline,
and cheap-first fixture gate tell maintainers whether those needs have
reviewable local evidence. This bridge joins those signals into one
metadata-only map so a high-priority user need cannot be treated as ready just
because a generic benchmark or public-source reference exists elsewhere.

The default `GET` call reports local fixture links and marks document/fact
evidence as `not_run` until sanitized structured outputs are submitted. The
`POST` call accepts local run metadata for:

- `document_benchmark_outputs`
- `document_fact_consistency_outputs`
- `cheap_first_gate`

It then reports which user needs are `ready`, `review_required`, `not_run`, or
`blocked`.

## What It Returns

- `summary`: need counts, ready/review/blocked/not-run counts, document and fact
  benchmark status, local baseline score, and cheap-first gate status
- `evidence_rows`: one row per user need with document case IDs, document type
  IDs, coverage-axis counts, document/fact result statuses, baseline statuses,
  public source IDs, calibration task IDs, reason codes, and next actions
- `source_summaries`: compact status from the user-need coverage map, document
  coverage, document evaluation, fact consistency evaluation, local rule
  baseline, and cheap-first gate
- `privacy_boundary`, `claim_boundary`, and `validation_commands`

## Safety

The bridge returns IDs, counts, statuses, and reason codes only. It does not
download public datasets, import public benchmark text, claim public benchmark
scores or production legal quality, call NewAPI, Gemini, OpenAI, Google,
gateways, models, or the network, change default models, or return raw legal
text, fixture snippets, document snippets, prompts, model outputs, payload
bodies, credentials, emails, phone numbers, identity numbers, or client
material.

## Validation

```bash
cd app/backend && python -m pytest tests/test_user_need_legal_document_benchmark_evidence.py -q
cd app/backend && python -m pytest tests/test_user_need_legal_document_benchmark_evidence.py tests/test_user_need_benchmark_coverage.py tests/test_legal_document_benchmark_suite.py tests/test_legal_document_benchmark_coverage.py tests/test_legal_document_benchmark_fixtures.py tests/test_legal_document_fact_consistency_benchmark.py tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py -q
cd app/frontend && npm run typecheck && npm run ui:regression
```

## Related Files

- `app/backend/services/user_need_legal_document_benchmark_evidence.py`
- `app/backend/tests/test_user_need_legal_document_benchmark_evidence.py`
- `app/backend/services/user_need_benchmark_coverage.py`
- `app/backend/services/legal_document_benchmark_suite.py`
- `app/backend/services/legal_document_benchmark_coverage.py`
- `app/backend/services/legal_document_benchmark_fixtures.py`
- `app/backend/services/legal_document_fact_consistency_benchmark.py`
- `app/backend/services/modelops_legal_fixture_cheap_first_benchmark_gate.py`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
