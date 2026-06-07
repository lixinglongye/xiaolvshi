# User Need Benchmark Coverage

`user_need_benchmark_coverage.py` maps user-needs radar items to local benchmark evidence.

## Endpoint

```http
GET /api/v1/maintenance/user-needs/benchmark-coverage
```

## Purpose

The user-needs radar ranks product needs, while the legal benchmark suite and fixture services prove low-resource validation coverage. This endpoint joins those artifacts so maintainers can see which high-priority needs already have local synthetic benchmark cases, fixtures, research backlog items, release gates, and public benchmark research mappings.

The endpoint also reads the metadata-only public benchmark sampler. This links LegalBench, CUAD, LexGLUE, LegalBench-RAG, LexEval, CaseGen, and Pile of Law source plans to each user need by local fixture IDs, local `ldoc-*` document fixture IDs, and benchmark case IDs. It reports whether those public sources are still `license_review_required`, `sampling_ready`, or `catalog_only`; it does not download or return external examples.

The endpoint also reads the Gemini/NewAPI cheap-first calibration service. Calibration rows are linked through each task's `user_need_ids`, so maintainers can see whether a user need is backed by passing selector replay, fixture, cost-guardrail, and cost-forecast evidence. The map returns calibration task IDs, release gates, status, and decisions only; it does not echo calibration payloads, prompts, gateway responses, or model output.

## What It Returns

- `status`: `ready` or `ready_with_gaps`
- `summary`: need counts, high-priority gap counts, benchmark case counts, fixture counts, backlog counts, public-source readiness counts, cheap-first calibration counts, sampler endpoint, and local-run policy
- `coverage_rows`: one row per user need with linked benchmark case IDs, synthetic fixture IDs, legal-document fixture IDs, public source IDs, public-source document fixture IDs, public sampling batch IDs, public sampling states, cheap-first calibration task IDs, calibration release gates, calibration decisions, research backlog item IDs, release gates, gap reasons, and next actions
- `gap_need_ids`, `high_priority_gap_need_ids`, `public_benchmark_gap_need_ids`, and `calibration_attention_need_ids`
- `source_summaries.public_sampler`, `source_summaries.public_sampler_resource_policy`, and `source_summaries.cheap_first_calibration`
- `recommended_actions`
- `privacy_boundary`
- `validation_commands`

The map reports planning coverage only. It does not claim production legal accuracy, public benchmark scores, external dataset runs, or real client-document validation.

## Implementation Priority Queue

`user-need-implementation-priority-queue` is the release/ledger/maintenance
evidence id for turning the coverage map into an execution queue. It joins
high-priority user needs, legal benchmark coverage gaps, cheap-first
calibration/model routing risk, and product execution actions for maintainer
review.

This queue is metadata-only. It does not download public datasets, call NewAPI,
Gemini, OpenAI, Google, gateways, or the network, write real env values, or
include raw legal text, prompts, payloads, model outputs, credentials, or public
benchmark samples.

## Gemini Route Coverage

`user-need-gemini-route-coverage` is the release/ledger/maintenance evidence id
for mapping user needs to Gemini cheap-first route evidence. It joins this
benchmark coverage map, cheap-first calibration task IDs, and
`modelops-gemini-cheap-first-route-preflight` rows so maintainers can see
Flash-Lite protected needs, premium/benchmark/license review gaps, and unmapped
route blockers.

This route coverage view is metadata-only. It does not download public
datasets, import public benchmark samples, call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, or the network, write configuration, change default
routes, shift traffic, or return raw legal text, prompts, route payloads, model
outputs, credentials, emails, or user identifiers.

## Safety

The service does not call NewAPI, Gemini, OpenAI, public benchmark sources, or a gateway. It does not return fixture snippets, raw benchmark samples, public benchmark text, calibration payloads, raw model output, user feedback text, credentials, emails, phone numbers, identity numbers, prompts, or client documents. It returns IDs, counts, release-gate links, decisions, and metadata-only status fields.

## Validation

```bash
python -m pytest tests/test_user_need_benchmark_coverage.py -q
python -m pytest tests/test_user_needs_radar.py tests/test_legal_review_benchmark.py tests/test_legal_document_benchmark_coverage.py tests/test_legal_public_benchmark_sampler.py tests/test_gemini_newapi_cheap_first_calibration.py tests/test_legal_research_backlog.py -q
```

## Related Files

- `app/backend/services/user_need_benchmark_coverage.py`
- `app/backend/tests/test_user_need_benchmark_coverage.py`
- `app/backend/services/user_needs_radar.py`
- `app/backend/services/legal_review_benchmark.py`
- `app/backend/services/legal_document_benchmark_coverage.py`
- `app/backend/services/legal_public_benchmark_sampler.py`
- `app/backend/services/gemini_newapi_cheap_first_calibration.py`
- `app/backend/services/user_need_gemini_route_coverage.py`
- `app/backend/services/legal_research_backlog.py`
- `app/backend/routers/maintenance.py`
- `docs/USER_NEED_GEMINI_ROUTE_COVERAGE.md`
