# ModelOps User-Need Cheap-First Handoff

`model_ops_user_need_cheap_first_handoff.py` builds a reviewer-facing handoff
packet for cheap-first Gemini/NewAPI default review. It aggregates:

- user-need benchmark coverage
- user-need implementation priority queue rows
- user-need Gemini route coverage
- the ModelOps user-need release bridge

The packet separates default-change blockers from maintainer-review-only rows
and highlights high-priority user needs already protected by cheap-first Gemini
routes such as Flash-Lite.

## Endpoints

- `/api/v1/aihub/models/user-need-cheap-first-handoff`
- `/api/v1/maintenance/user-needs/cheap-first-evidence-handoff`
- `/api/v1/aihub/models` as `user_need_cheap_first_handoff`

## Boundaries

This handoff is metadata-only. It does not call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, public datasets, or the network. It does not write
configuration, change default routes, shift traffic, claim public benchmark
scores, or return raw legal text, benchmark samples, fixture snippets, prompts,
model outputs, payloads, headers, emails, identifiers, or credentials.

## Review Rules

- Blocked handoff rows prevent cheap-first default promotion.
- Review rows require maintainer signoff before release claims.
- Ready rows support current cheap-first defaults, but do not change routes.
- Premium exceptions and public benchmark license concerns stay review-only
  until a maintainer records safe evidence.

## Validation

```bash
python -m pytest tests/test_model_ops_user_need_cheap_first_handoff.py tests/test_model_ops_user_need_release_bridge.py -q
python -m pytest tests/test_user_need_implementation_priority_queue.py tests/test_user_need_gemini_route_coverage.py tests/test_user_need_benchmark_coverage.py -q
python -m pytest tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```
