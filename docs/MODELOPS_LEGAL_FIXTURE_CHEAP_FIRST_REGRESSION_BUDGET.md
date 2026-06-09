# ModelOps Legal Fixture Cheap-First Regression Budget

`modelops-legal-fixture-cheap-first-regression-budget` is a metadata-only
review packet for cheap-first legal default changes.

It joins four existing local signals:

- `legal_fixture_regression`
- `legal_fixture_cheap_first_benchmark_gate`
- `legal_fixture_cheap_first_default_promotion_packet`
- `small_legal_document_benchmark_runbook_evidence`

The service is designed for low-resource machines. It keeps
`max_parallel_requests` at `1`, returns fixture ids and status counts only, and
never runs a model or gateway.

## API

- `GET /api/v1/aihub/models/legal-fixture-cheap-first-regression-budget`
- `POST /api/v1/aihub/models/legal-fixture-cheap-first-regression-budget`
- Aggregate field: `legal_fixture_cheap_first_regression_budget`

## Review Policy

The budget blocks default-change evidence when fixture regression comparison
finds new blockers, benchmark gate evidence is blocked, or the promotion packet
is blocked.

Passing fixture rows still require maintainer review. The packet never writes
configuration, shifts traffic, claims maintainer approval, or allows an
automatic default change.

## Privacy Boundary

The packet returns fixture ids, source statuses, counts, cost deltas, reason
codes, and review actions only. It does not return raw legal text, fixture
snippets, prompts, generated document text, model outputs, gateway payloads,
credentials, emails, or approvals.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_modelops_legal_fixture_cheap_first_regression_budget.py tests/test_legal_fixture_regression.py tests/test_model_ops_cheap_first_release_decision.py tests/test_model_ops_readiness.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```
