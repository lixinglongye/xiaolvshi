# Model Catalog Candidate Impact Replay

`model-catalog-candidate-impact-replay` is a metadata-only ModelOps evidence gate for reviewing new Gemini catalog candidates before maintainers edit defaults.

## Purpose

The replay answers one question: if sanitized candidate `ModelProfile` metadata were added to the local Gemini catalog in memory, which cheap-first task defaults would change?

It does not approve, persist, or deploy those changes. Maintainers still need official model list, lifecycle, pricing, capability, and gateway probe evidence before editing `model_catalog.py` or changing runtime defaults.

## Inputs

The service accepts sanitized candidate metadata only:

- Gemini-like model id
- lifecycle status
- cost and latency tiers
- token or image price metadata
- capabilities and best-for tags
- context window metadata

It can also reuse candidate rows from the catalog candidate patch plan as review-only replay sources.

## Safety Boundary

The replay is intentionally inert:

- Does not edit `model_catalog.py`
- Does not write `.env`, template, runtime configuration, approval, or traffic state files
- Does not call NewAPI, Gemini, OpenAI, Google, a gateway, or the network
- Does not store POST payloads as persistent state
- Does not echo raw prompts, messages, legal text, model output, headers, credentials, emails, or raw payloads

Outputs are limited to sanitized model ids, lifecycle/cost metadata, task impact rows, reason codes, privacy flags, claim boundaries, and validation commands.

## Status Semantics

- `monitor_only`: no candidate profile has been supplied; the required readiness component should not block release.
- `ready`: sanitized stable token-priced low-cost text/json candidates replay successfully.
- `review_required`: candidates are preview, unpriced, media-specific, premium, or otherwise need maintainer review.
- `blocked`: input contains forbidden fields, sensitive values, non-Gemini ids, or missing required metadata.

## Official Price And Status Gate

Impact replay must keep candidates with unconfirmed official provider or
gateway pricing, lifecycle status, or availability as `unpriced` and
`review-only`. It must not hard-code costs, count savings, or recommend default
promotion until source-backed price, status, capability, and gateway evidence
are refreshed.

## Validation

Run the focused backend checks:

```powershell
cd app/backend
python -m pytest tests/test_model_catalog_candidate_impact_replay.py tests/test_model_default_candidate_selector.py tests/test_model_capability_matrix.py -q
```

Run the release/UI gate set when touching the ModelOps page:

```powershell
cd app/backend
python -m pytest tests/test_model_catalog_candidate_impact_replay.py tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```
