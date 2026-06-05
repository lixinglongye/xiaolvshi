# User Need Benchmark Coverage

`user_need_benchmark_coverage.py` maps user-needs radar items to local benchmark evidence.

## Endpoint

```http
GET /api/v1/maintenance/user-needs/benchmark-coverage
```

## Purpose

The user-needs radar ranks product needs, while the legal benchmark suite and fixture services prove low-resource validation coverage. This endpoint joins those artifacts so maintainers can see which high-priority needs already have local synthetic benchmark cases, fixtures, research backlog items, and release gates.

## What It Returns

- `status`: `ready` or `ready_with_gaps`
- `summary`: need counts, high-priority gap counts, benchmark case counts, fixture counts, backlog counts, and local-run policy
- `coverage_rows`: one row per user need with linked benchmark case IDs, synthetic fixture IDs, legal-document fixture IDs, research backlog item IDs, release gates, gap reasons, and next actions
- `gap_need_ids` and `high_priority_gap_need_ids`
- `recommended_actions`
- `privacy_boundary`
- `validation_commands`

The map reports planning coverage only. It does not claim production legal accuracy, public benchmark scores, external dataset runs, or real client-document validation.

## Safety

The service does not call NewAPI, Gemini, OpenAI, public benchmark sources, or a gateway. It does not return fixture snippets, raw benchmark samples, raw model output, user feedback text, credentials, emails, phone numbers, identity numbers, prompts, or client documents. It returns IDs, counts, release-gate links, and metadata-only status fields.

## Validation

```bash
python -m pytest tests/test_user_need_benchmark_coverage.py -q
python -m pytest tests/test_user_needs_radar.py tests/test_legal_review_benchmark.py tests/test_legal_document_benchmark_coverage.py tests/test_legal_research_backlog.py -q
```

## Related Files

- `app/backend/services/user_need_benchmark_coverage.py`
- `app/backend/tests/test_user_need_benchmark_coverage.py`
- `app/backend/services/user_needs_radar.py`
- `app/backend/services/legal_review_benchmark.py`
- `app/backend/services/legal_document_benchmark_coverage.py`
- `app/backend/services/legal_research_backlog.py`
- `app/backend/routers/maintenance.py`
