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
- `openrouter/google/gemini-2.5-flash-lite`

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
- Sensitive observed values are replaced with `redacted-sensitive-model-id-*`
  rows and counted in `rejected_sensitive_count`.
- The endpoint never writes `.env`, changes model defaults, shifts traffic, or
  calls a gateway.

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

Only sanitized model id metadata is returned. Raw prompts, legal text, gateway
payloads, credentials, emails, and raw model outputs are not accepted as
evidence and are not echoed.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_gemini_newapi_model_alias_matrix.py tests/test_gemini_newapi_model_selector.py tests/test_model_catalog.py -q
python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q
```

Run from `app/frontend` after the maintenance UI is updated:

```powershell
npm run typecheck
npm run ui:regression
```
