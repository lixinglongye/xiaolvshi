# ModelOps Observed Gemini Premium Exception Review

This packet is metadata-only release evidence for observed Gemini Pro or premium variants.
It exists to keep cheap-first defaults protected while still giving maintainers a clear
path to review explicit premium exceptions.

## Scope

- Join observed Gemini intake rows with coverage-gap rows.
- Classify Pro or premium variants as `premium_exception_review`.
- Allow only explicit premium routes after maintainer and cost-owner review.
- Keep cheap, fast, OCR, classification, agentic, and grounded-research defaults off premium variants.
- Surface release checks for sanitized intake, explicit-route boundaries, high-frequency default blocks, and no automatic configuration changes.

## Non-Goals

- No NewAPI, Gemini, OpenAI, Google, gateway, app-AI, or network calls.
- No configuration writes, default changes, or traffic shifts.
- No raw prompts, request bodies, response bodies, payloads, legal text, model outputs, emails, credentials, or user identifiers.
- No pricing accuracy, model quality, gateway availability, or account inventory claims.

## Local Validation

```powershell
cd app/backend
python -m pytest tests/test_model_ops_observed_gemini_premium_exception_review.py -q
python -m pytest tests/test_model_ops_observed_gemini_premium_exception_review.py tests/test_model_ops_observed_gemini_coverage_gap_queue.py tests/test_model_ops_observed_gemini_model_intake_queue.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q
```
