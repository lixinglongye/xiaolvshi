# Model Cost Regression Snapshots

This document describes the local cost regression snapshot service for model
routing. It is designed for release checks before changing model defaults,
gateway configuration, or catalog pricing.

## Scope

- Service: `services.model_cost_regression_snapshots.ModelCostRegressionSnapshotService`
- Test: `tests/test_model_cost_regression_snapshots.py`
- Network: none
- Credentials: none
- Inputs: fixed synthetic model tasks, monthly volumes, token shapes, escalation
  rates, and local catalog model ids

## Output Contract

`build_snapshots()` returns:

- `status`: `pass`, `warn`, or `fail`
- `summary`: snapshot count, pass/warn/fail counts, aggregate cheap-first cost,
  premium-only baseline cost, estimated savings, cost forecast status, and
  routing replay status
- `snapshots`: fixed task snapshots for fast routing, classification, OCR,
  review, and large PDF premium exception paths
- `regression_checks`: cross-snapshot checks for cost forecast coverage,
  routing replay health, and high-volume default tiers
- `recommended_actions`: release actions for warnings or failures
- `privacy_note`: explicit data boundary
- `validation_commands`: small local pytest command

## Snapshot Method

Each snapshot compares the current cheap-first route against a premium-only
baseline:

1. Resolve the current initial model from the local model catalog defaults.
2. Resolve the escalation model from the deterministic escalation policy.
3. Resolve the premium-only baseline from the premium PDF alias.
4. Estimate unit token cost from local catalog pricing.
5. Estimate monthly cheap-first cost using fixed monthly volume and escalation
   rate.
6. Compare cheap-first cost with the premium-only baseline.
7. Apply savings, monthly cost, and initial cost-tier drift thresholds.

No prompt text, legal document content, user identity, API key, or gateway
credential is read or stored.

## Fixed Scenarios

| Snapshot | Task | Monthly Units | Purpose |
| --- | --- | ---: | --- |
| `fast-routing-5000` | `fast` | 5,000 | Guards preflight, routing, and light extraction defaults. |
| `classification-2500` | `classification` | 2,500 | Guards material classification before review. |
| `ocr-extraction-3500` | `ocr` | 3,500 | Guards page or chunk level OCR assist costs. |
| `review-quality-450` | `review` | 450 | Guards balanced legal review and premium escalation rates. |
| `pdf-premium-exception-80` | `pdf` | 80 | Keeps explicit premium PDF review volume visible. |

## Drift Thresholds

The service checks three main cost signals:

- Savings ratio: warning below `warn_min_savings_ratio`, failure below
  `fail_min_savings_ratio`
- Monthly cost: warning above `warn_max_monthly_cost_usd`, failure above
  `fail_max_monthly_cost_usd`
- Initial cost tier: failure when the initial route exceeds
  `max_initial_cost_tier`; unknown catalog models warn because billing is not
  locally priced

High-volume defaults for fast, classification, and OCR are also checked across
snapshots and must stay in the `lowest` or `low` cost tiers.

## Local Validation

```powershell
cd D:\小律师\app\backend
python -m pytest tests/test_model_cost_regression_snapshots.py -q
```

The tests cover default pass behavior, warning thresholds, premium drift
failures, savings calculations, and absence of sensitive values in the service
payload.
