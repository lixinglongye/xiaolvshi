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
- Preview, unpriced, premium, and media-route models stay explicit or review-only unless their task policy allows them.

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
