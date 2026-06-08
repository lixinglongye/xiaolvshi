# ModelOps Cheap-First Cascade Research Gate

`model_ops_cheap_first_cascade_research_gate.py` adds a metadata-only release
gate for cheap-first Gemini/NewAPI cascade strategy.

## Endpoint

```http
GET /api/v1/aihub/models/cheap-first-cascade-research-gate
POST /api/v1/aihub/models/cheap-first-cascade-research-gate
```

The full `/api/v1/aihub/models` payload also includes
`cheap_first_cascade_research_gate`. `model_ops_readiness` treats it as
required release evidence.

## What It Aggregates

- FrugalGPT-style cost-aware cascade justification.
- Official Gemini Flash-Lite cheap-start positioning and pricing links.
- Local `route_quality_budget` quality gates.
- Local `cheap_first_escalation_budget` cost and premium-review thresholds.
- Local `failure_upgrade_budget` attempt, quota, and incremental-cost rules.
- Cheap-first calibration and user-need handoff evidence.

## Non-Claims

This gate does not call NewAPI, Gemini, OpenAI, Google, gateways, model
endpoints, public datasets, or the network. It does not write configuration,
change default routes, shift traffic, claim production accuracy, claim public
benchmark scores, or prove 24-hour completion.

## Privacy Boundary

Only source ids, source statuses, check ids, research URLs, counts, and policy
labels are returned. The service rejects sensitive field names and secret-like
values without echoing them. It must not return prompts, messages, legal text,
document text, headers, request bodies, response bodies, model output, emails,
phone numbers, identity numbers, API keys, or credentials.

## Research Anchors

- FrugalGPT motivates starting with cheaper models and escalating only when the
  cascade needs stronger capability: <https://arxiv.org/abs/2305.05176>
- Gemini model documentation describes Flash-Lite as the cheap-start model for
  high-throughput work: <https://ai.google.dev/models/gemini>
- Gemini API pricing gives the official provider pricing surface:
  <https://ai.google.dev/gemini-api/docs/pricing>

## Validation

```bash
cd app/backend
python -m pytest tests/test_model_ops_cheap_first_cascade_research_gate.py tests/test_model_route_quality_budget.py tests/test_model_ops_cheap_first_escalation_budget.py tests/test_model_failure_upgrade_budget.py tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py -q
```

## Related Files

- `app/backend/services/model_ops_cheap_first_cascade_research_gate.py`
- `app/backend/tests/test_model_ops_cheap_first_cascade_research_gate.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/routers/aihub.py`
