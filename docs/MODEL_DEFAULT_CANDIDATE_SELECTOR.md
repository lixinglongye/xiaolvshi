# Model Default Candidate Selector

`model_default_candidate_selector.py` adds a local, metadata-only selector for Gemini/NewAPI default candidates.

## Purpose

The selector derives cheapest capable task recommendations from the local Gemini catalog instead of hard-coding every recommendation to one model id. It ranks catalog rows by:

- required capabilities
- lifecycle status
- local price metadata
- cost tier
- latency tier
- preferred capability matches

This keeps runtime defaults stable while giving ModelOps evidence a way to spot a future lower-cost stable Flash-Lite candidate before maintainers edit `.env` files or templates.

## Boundaries

- It does not call NewAPI, Gemini, OpenAI, Google, gateways, or the network.
- It does not write configuration, `.env`, secrets, or traffic-shift state.
- It does not include prompts, legal text, payload bodies, model output, account data, or credentials.
- Default ladders must distinguish directly promotable `default_eligible`
  candidates from `review-only` candidates.
- Preview, unpriced, premium-over-budget, premium-exception, unknown,
  deprecated, and media-route models stay explicit or `review-only` unless
  their task policy and source-backed metadata explicitly make them
  `default_eligible`.

## Default Eligibility Contract

The selector may expose a task ladder that includes default candidates,
verification candidates, fallbacks, premium exceptions, and review context. The
ladder itself is not a promotion list. It must be read as two sets:

- `default_eligible`: stable, priced, catalog-known, gateway-compatible,
  lifecycle-current candidates that satisfy the task capability requirements,
  fit the task cost ceiling, and are not preview, deprecated, unknown,
  unpriced, premium-over-budget, or premium-exception-only.
- `review-only`: preview, unpriced, unknown or catalog-review, deprecated,
  premium-over-budget, premium-exception-only, media-route mismatch, missing
  capability, or operator-review-required candidates.

UI surfaces and maintainer runbooks may suggest env/default promotion only from
the `default_eligible` set. `review-only` rows may be shown for context,
explicit experiments, gateway probes, fallbacks, or manual review, but they must
not be rendered as directly promotable defaults.

## Official Price And Status Gate

If official provider or gateway pricing, lifecycle status, or model availability
has not been confirmed, the selector must keep the model `unpriced` and
`review-only`. Do not hard-code costs, use it in cheap-first savings claims, or
promote it as a `default_eligible` candidate until source-backed price, status,
capability, and gateway evidence are refreshed.

## Current Behavior

- High-frequency tasks still recommend `gemini-2.5-flash-lite`.
- Legal review still recommends `gemini-2.5-flash`.
- Agentic and grounded-research tasks still recommend `gemini-3.1-flash-lite`.
- Image routes still recommend `gemini-2.5-flash-image`, with `gemini-3.1-flash-image` visible as a priced media candidate.
- A simulated cheaper stable `gemini-4.0-flash-lite` catalog row is promoted by the selector in tests, while preview or unpriced variants are rejected for default use.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_model_default_candidate_selector.py tests/test_model_catalog.py tests/test_gemini_newapi_cheap_first_policy.py tests/test_gemini_newapi_model_selector.py tests/test_model_price_refresh_monitor.py tests/test_model_capability_matrix.py -q
```
