# User Need Gemini Route Coverage

`user_need_gemini_route_coverage.py` maps user-needs radar items to Gemini
cheap-first routing evidence.

## Endpoint

```http
GET /api/v1/maintenance/user-needs/gemini-route-coverage
GET /api/v1/aihub/models/user-need-gemini-route-coverage
```

## Purpose

The user-needs radar says what product work matters. The benchmark coverage map
shows which needs have local legal-document and public-benchmark planning
evidence. The Gemini route preflight shows whether high-frequency tasks stay on
stable cheap-first Flash-Lite routes while premium, preview, media, unknown, or
unpriced variants remain review-only.

This endpoint joins those three views so maintainers can review each need with
the route task source, linked route tasks, default models, cost tiers, release
actions, blockers, and next actions in one place.

The evidence is rendered on both `/maintenance` and `/model-ops`. The ModelOps
view uses the AIHub direct endpoint so route reviewers can inspect user-need
coverage next to release-bridge and cheap-first handoff controls without
opening the broader maintenance page.

## What It Returns

- `status`: `ready`, `review_required`, or `blocked`
- `summary`: user-need counts, high-priority route protection, cheap-first,
  balanced, premium-exception, review, blocked, source, and boundary counts
- `coverage_rows`: one row per user need with linked calibration task IDs,
  linked route tasks, default models, route modes, cost tiers, benchmark status,
  public benchmark status, route coverage status, review reasons, blockers, and
  next actions
- `blocked_need_ids`, `review_need_ids`, and `unmapped_need_ids`
- `source_summaries`, `source_boundaries`, `privacy_boundary`, and
  `claim_boundary`
- `validation_commands`

## Safety Boundary

The service is metadata-only. It does not download public datasets, import
public benchmark samples, call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, or the network, write configuration, change default routes, shift
traffic, claim public benchmark scores, or claim live gateway validation.

It does not return raw legal text, prompts, route payloads, request bodies,
response bodies, headers, model outputs, gateway responses, credentials, emails,
or user identifiers.

## Validation

```bash
python -m pytest tests/test_user_need_gemini_route_coverage.py -q
python -m pytest tests/test_user_need_gemini_route_coverage.py tests/test_model_ops_gemini_cheap_first_route_preflight.py tests/test_user_need_benchmark_coverage.py -q
python -m pytest tests/test_user_need_gemini_route_coverage.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
```

Frontend checks:

```bash
cd app/frontend
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/user_need_gemini_route_coverage.py`
- `app/backend/tests/test_user_need_gemini_route_coverage.py`
- `app/backend/services/user_need_benchmark_coverage.py`
- `app/backend/services/gemini_newapi_cheap_first_calibration.py`
- `app/backend/services/model_ops_gemini_cheap_first_route_preflight.py`
- `app/backend/routers/aihub.py`
- `app/backend/routers/maintenance.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
