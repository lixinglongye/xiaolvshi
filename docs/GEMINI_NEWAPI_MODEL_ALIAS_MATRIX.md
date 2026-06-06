# Gemini/NewAPI Model Alias Matrix

This document defines the metadata-only maintenance endpoint for reviewing
OpenAI-compatible Gemini model id aliases before they are used in cheap-first
defaults.

## Endpoint

```http
GET /api/v1/maintenance/gemini-newapi-model-alias-matrix
POST /api/v1/maintenance/gemini-newapi-model-alias-matrix
```

The endpoint is implemented by
`app/backend/services/gemini_newapi_model_alias_matrix.py` and is exposed through
`app/backend/routers/maintenance.py`.

## Purpose

Different OpenAI-compatible gateways can expose the same Gemini model with
different names, for example:

- `gemini-2.5-flash-lite`
- `models/gemini-2.5-flash-lite`
- `google/gemini-2.5-flash-lite`
- `google:gemini-2.5-flash-lite`
- `yibu/gemini-2.5-flash-lite`
- `yibuapi/google/gemini-2.5-flash-lite`
- `newapi/google/gemini-2.5-flash-lite`
- `openrouter/google/gemini-2.5-flash-lite`
- `publishers/google/models/gemini-2.5-flash-lite`

The alias matrix maps those sanitized ids back to the local catalog id, cost
tier, lifecycle status, cheap-first default eligibility, and premium/manual
review boundary. Unknown Gemini-like ids are marked for catalog review and
external ids are kept out of Gemini defaults.

## Default Policy

- Stable Flash-Lite catalog aliases can be high-frequency cheap-first
  candidates.
- Stable Flash aliases can support balanced review routes after cheap precheck.
- Pro, preview, image, unknown Gemini-like, and external aliases require
  explicit maintainer review before default use.
- Gemini 3 Flash Preview aliases can resolve to catalog metadata, but preview
  lifecycle keeps them review-only.
- Gemini 3.5 Flash is treated as an unpriced premium-posture Flash variant
  until official provider or gateway pricing is confirmed, not a cheap-first
  high-frequency default.
- Sensitive observed values are replaced with `redacted-sensitive-model-id-*`
  rows and counted in `rejected_sensitive_count`.
- Malformed observed values without supported model-id fields are replaced with
  `redacted-invalid-model-id-*` rows and counted in
  `rejected_invalid_count`. `rejected_model_count` is the total blocking count
  used for sanitization posture.
- The endpoint never writes `.env`, changes model defaults, shifts traffic, or
  calls a gateway.

## Official Price And Status Gate

Alias rows whose official provider or gateway pricing, lifecycle status, or
availability has not been confirmed must remain `unpriced` and `review-only`.
Do not hard-code costs, count those aliases in cheap-first savings, or allow
default promotion until source-backed price, status, capability, and gateway
evidence are refreshed.

## POST Payload

```json
{
  "include_catalog_aliases": false,
  "observed_models": [
    "models/gemini-2.5-flash-lite",
    "yibu/gemini-3.1-flash-lite",
    "google/gemini-3.2-flash-lite",
    "vendor/other-model"
  ]
}
```

Only sanitized model id metadata and rejection counts are returned. Raw prompts,
legal text, gateway payloads, malformed source rows, credentials, emails, and
raw model outputs are not accepted as evidence and are not echoed.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_gemini_newapi_model_alias_matrix.py tests/test_gemini_newapi_model_selector.py tests/test_model_catalog.py -q
python -m pytest tests/test_model_catalog.py tests/test_gemini_newapi_model_alias_matrix.py tests/test_gemini_newapi_alias_capability_coverage.py tests/test_gemini_model_variant_matrix.py tests/test_model_catalog_source_audit.py -q
python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q
```

Run from `app/frontend` after the maintenance UI is updated:

```powershell
npm run typecheck
npm run ui:regression
```
