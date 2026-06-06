# ModelOps Legal Benchmark Risk Bridge

`modelops-legal-benchmark-risk-bridge` brings the maintenance-side legal
benchmark route-risk queue into the ModelOps reviewer surface.

## Purpose

The bridge gives maintainers one ModelOps panel for reviewing whether legal
review routes can stay cheap-first, need a balanced precheck, or must remain a
premium operator exception.

It summarizes existing metadata from:

- the model route legal benchmark risk queue
- cheap-first release decision evidence
- default-change queue metadata
- user-need benchmark coverage rows

## Endpoint

```http
GET /api/v1/aihub/models/legal-benchmark-risk-bridge
```

The full `/api/v1/aihub/models` payload also includes
`legal_benchmark_risk_bridge`, and `/model-ops` renders it between the failure
upgrade budget and cheap-first escalation budget panels.

## Returned Evidence

- route review count, user-need review count, watch routes, and blockers
- cheap-first allowed route count and balanced-precheck count
- premium exception and public benchmark license-watch counts
- route review rows with task ids, source ids, reason codes, and actions
- user-need rows with route coverage and implementation actions
- bridge policy for default promotion and premium exception boundaries

## Boundaries

This evidence is metadata only. It does not:

- call NewAPI, Gemini, OpenAI, Google, or any gateway
- run model probes or consume quota
- download public benchmark datasets
- write configuration, shift traffic, or change defaults
- claim public benchmark scores or leaderboard rank
- return raw legal text, benchmark samples, fixture snippets, prompts, model
  output, gateway payloads, headers, client identifiers, emails, or credentials

## Review Policy

- Current cheap-first defaults can remain allowed only when there are no route
  blockers.
- New default promotion is allowed only when the bridge status is `pass`.
- Premium routes are never default-allowed by this bridge; they remain explicit
  operator exceptions.
- Public benchmark mappings require license and attribution review before they
  can support release claims.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_model_ops_legal_benchmark_risk_bridge.py tests/test_model_route_legal_benchmark_risk_queue.py tests/test_frontend_ui_regression_gate.py -q
```

Frontend validation:

```powershell
cd ../frontend
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/model_ops_legal_benchmark_risk_bridge.py`
- `app/backend/tests/test_model_ops_legal_benchmark_risk_bridge.py`
- `app/backend/services/model_route_legal_benchmark_risk_queue.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/frontend_ui_regression_gate.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
