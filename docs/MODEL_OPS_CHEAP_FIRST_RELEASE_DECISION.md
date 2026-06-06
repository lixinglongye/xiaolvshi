# ModelOps Cheap-First Release Decision

This packet gives maintainers one metadata-only decision point before changing
Gemini/NewAPI cheap-first defaults.

## Purpose

`cheap_first_release_decision` combines upstream ModelOps evidence into a
default-promotion decision. It helps keep the current cheap-first defaults in
place while making catalog drift, missing pricing, route-quality gaps,
single-failure retry-up risk, escalation-budget drift, and performance warnings
visible before a new model is promoted.

The packet is downstream of `model_ops_readiness`. It does not feed back into
readiness and does not add another readiness component.

## Endpoint

```http
GET /api/v1/aihub/models/cheap-first-release-decision
```

The full `/api/v1/aihub/models` payload also includes
`cheap_first_release_decision`.

`default_change_queue` consumes this packet downstream and turns proposed
cheap-first default edits into `ready`, `review_required`, `blocked`, or
`no_action` queue items.

`POST /api/v1/aihub/models/performance-budget` also returns a fresh release
decision computed with the submitted sanitized timing observations. A warning
performance budget requires maintainer review, and a failing performance budget
blocks cheap-first default promotion in the same response and in subsequent
in-process `/api/v1/aihub/models` aggregate payloads.

## Inputs

The service consumes existing signal metadata only:

- `model_ops_readiness`
- `cheap_first_calibration`
- `gemini_variant_matrix`
- `catalog_source_audit`
- `route_quality_budget`
- `failure_upgrade_budget`
- `cheap_first_escalation_budget`
- `price_refresh_monitor`
- `model_ops_performance_budget`

It reads status fields, check IDs, counts, and recommended actions. It does not
rerun model calls, gateway probes, price scrapes, benchmark downloads, or legal
document review jobs.

## Decision Logic

- If any required source signal is missing, failed, or carries blocking check
  IDs, the packet returns `fail` and blocks default promotion.
- If no source blocks but at least one source warns, the packet returns
  `review_required`. Current cheap-first defaults can stay in place, but new
  default promotion requires maintainer review.
- If every source passes, the packet returns `pass` and allows default changes
  after the normal release validation commands pass.

The frontend `/model-ops` page displays the decision, source signal table,
default-promotion status, and privacy boundary.

The packet also exposes `claim_boundary` booleans for common over-claims such
as live gateway execution, public benchmark scores, external adoption, 24-hour
completion, and production accuracy. These fields are always false unless a
future implementation adds separate proof for those claims.

## Allowed Claims

Maintainers can claim that the project has a metadata-only decision packet for
reviewing cheap-first default changes. They can also claim that the packet
aggregates existing ModelOps readiness, calibration, catalog, route-quality,
failure-upgrade-budget, escalation-budget, price-refresh, and performance-budget
signals.

## Must Not Claim

This packet does not prove:

- live gateway health
- NewAPI, Gemini, OpenAI, or Google account status
- public benchmark scores
- production traffic coverage
- real client legal accuracy
- 24-hour continuous session completion
- external adoption or maintainer activity outside this repository

## Privacy Boundary

The packet returns only source keys, status values, check IDs, counts, policy
labels, and recommended maintainer actions. It must not include credentials,
request headers, prompts, emails, raw legal text, copied benchmark samples, raw
model output, or raw gateway responses.

## Validation

Run:

```powershell
cd app/backend
python -m pytest tests/test_model_ops_cheap_first_release_decision.py tests/test_model_ops_readiness.py tests/test_model_catalog_source_audit.py tests/test_model_route_quality_budget.py tests/test_model_ops_cheap_first_escalation_budget.py tests/test_model_failure_upgrade_budget.py tests/test_model_default_candidate_selector.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```

Related files:

- `app/backend/services/model_ops_cheap_first_release_decision.py`
- `app/backend/tests/test_model_ops_cheap_first_release_decision.py`
- `app/backend/services/model_ops_cheap_first_escalation_budget.py`
- `app/backend/tests/test_model_ops_cheap_first_escalation_budget.py`
- `app/backend/services/model_failure_upgrade_budget.py`
- `app/backend/tests/test_model_failure_upgrade_budget.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
- `docs/MODEL_FAILURE_UPGRADE_BUDGET.md`
