# Legal Benchmark Research Refresh

This release evidence tracks a metadata-only backend feature for refreshing the
local legal benchmark research plan. It is meant to sit beside the existing
LegalBench, LexGLUE, COLIEE registry and the adoption research bridge.

## Scope

Expected evidence paths:

- `app/backend/services/legal_benchmark_research_refresh.py`
- `app/backend/tests/test_legal_benchmark_research_refresh.py`
- `app/backend/services/legal_benchmark_research_registry.py`
- `app/backend/services/legal_adoption_research_bridge.py`
- `docs/LEGAL_BENCHMARK_RESEARCH_REFRESH.md`

The refresh should record source names, source URLs, refresh cadence labels,
review status, local mapping changes, release gate links, validation commands,
and non-claim guardrails. It should update planning metadata only.

## Endpoints

```http
GET /api/v1/maintenance/legal-benchmark-research-refresh
GET /api/v1/maintenance/legal-review-benchmark/research-refresh
```

The response should be a reviewer-safe metadata payload with source metadata,
refresh rows, user-need mappings, recommended actions, privacy boundaries,
claim boundaries, and local validation commands.

## Non-Claims

This feature does not:

- download LegalBench, LexGLUE, COLIEE, or other public benchmark datasets
- publish or imply public benchmark scores, leaderboard rank, or parity
- import, store, or echo external legal text or benchmark examples
- call models, gateways, NewAPI, Gemini, OpenAI, or other providers
- read, write, validate, or expose credentials
- prove law-firm adoption, production legal quality, survey results, or 24-hour maintenance completion

## Release Evidence

The release gate is optional, matching the current legal benchmark research
registry and adoption bridge checks. A missing or not-run refresh check must not
block release by itself. It should only help reviewers see whether research
planning metadata is current.

Suggested validation command:

```powershell
cd app/backend
python -m pytest tests/test_legal_benchmark_research_refresh.py tests/test_legal_benchmark_research_registry.py tests/test_legal_adoption_research_bridge.py -q
```

## Maintenance Evidence

The continuous update ledger records `legal-benchmark-research-refresh` as a
medium benchmark slice. The ledger entry is evidence of release/maintenance
tracking only; it does not make the 24-hour continuous maintenance target
complete and does not change benchmark coverage claims.

The OSS maintenance profile may cite this as repository-backed benchmark
planning evidence only. Public-facing wording should say the repository has a
metadata-only refresh plan for local synthetic benchmark mapping, not that it
has run external benchmarks.

## Related Docs

- `docs/LEGAL_ADOPTION_RESEARCH_BRIDGE.md`
- `docs/LEGAL_DOCUMENT_BENCHMARK_COVERAGE.md`
- `docs/CONTINUOUS_UPDATE_LEDGER.md`
- `docs/FRONTEND_UI_REGRESSION_GATE.md`
- `docs/OSS_MAINTENANCE_EVIDENCE.md`
