# Model Price Refresh Monitor

## Purpose

`ModelPriceRefreshMonitorService` is a local-only maintenance monitor for
Gemini and OpenAI-compatible gateway model pricing drift. It checks whether the
high-volume defaults still point at the lowest priced capable Gemini model and
whether observed gateway models need a catalog refresh before becoming defaults.
It also checks media defaults such as image generation, where per-image pricing
matters more than token pricing.

The monitor does not call Gemini, NewAPI, OpenAI, or any external network. It
only reads local metadata from:

- `app/backend/services/model_catalog.py`
- `app/backend/services/model_cost_forecast.py`

## Service

File:

- `app/backend/services/model_price_refresh_monitor.py`

Main entry point:

- `ModelPriceRefreshMonitorService.build_monitor(observed_models=None, cost_forecast=None)`

The returned payload includes:

- `status`
- `summary`
- `checks`
- `drift_signals`
- `recommended_actions`
- `privacy_note`
- `validation_commands`

## Checks

### High-Frequency Defaults

The monitor checks these high-volume tasks:

- `fast`
- `classification`
- `ocr`

Each task must remain on a known, stable, token-priced, lowest-tier model. The
expected default is:

- `gemini-2.5-flash-lite`

If one of these defaults points at an unknown, preview, Pro, premium, unpriced,
or higher-tier model, the monitor returns `fail`.

### Cost Forecast Pricing

The monitor reviews the local cost forecast rows and checks each referenced
model:

- `initial_model`
- `escalation_model`
- `premium_baseline_model`

Known forecast models must have local price metadata. Missing or unknown pricing
returns `warn` so maintainers refresh the local catalog before using the row for
budget decisions.

### Media Defaults

The monitor checks media task defaults separately from high-volume text tasks.
The current media task is:

- `image`

`APP_AI_IMAGE_MODEL` must resolve to a known, stable Gemini image model with
`output_usd_per_image` metadata. The expected default is:

- `gemini-2.5-flash-image`

If the image default points to an unknown, preview, Pro, premium, unpriced, or
non-image model, the monitor returns `fail` so maintainers refresh pricing or
restore the lower-cost media default before increasing image usage.

### Observed Gateway Models

`observed_models` can contain model ids from a gateway model list, request log,
or local fixture. The monitor accepts strings or dictionaries with `id`,
`model`, or `name`.

Observed Gemini-like models return `warn` when they are:

- unknown to the local catalog
- preview
- Pro or premium
- missing price metadata

Warned models should stay explicit-only until maintainers confirm tier,
stability, and gateway price.

### Official Price And Status Gate

If official provider or gateway pricing, lifecycle status, or model availability
has not been confirmed, the monitor must treat the model as `unpriced` and
`review-only`. Do not fill in guessed token or image costs, use the model in
savings claims, or recommend it as a default until source-backed price, status,
capability, and gateway evidence are refreshed.

### Catalog Watchlist

Preview, premium, or unpriced catalog entries are listed in `drift_signals` with
info severity. They do not fail the monitor by themselves because they may be
valid explicit exceptions.

## Privacy Boundary

The monitor must contain only routing and pricing metadata. It must not return:

- gateway credentials
- prompts
- legal documents
- client identifiers
- raw model outputs

Observed model ids are redacted when they look like credentials or contact data.

## Low-Resource Validation

## Model Ops Integration

The monitor is now part of the main `GET /api/v1/aihub/models` payload as
`price_refresh_monitor`. `ModelOpsReadinessService` treats it as a required
cost component, so a failing high-frequency default or an unreviewed pricing
drift can block model-ops release readiness before the UI promotes a new
Gemini/NewAPI default.

The frontend `/model-ops` page shows:

- monitor status, blocking count, warning count, drift signal count, and the
  high-frequency cheap-first tasks
- media tasks covered by per-image price checks
- each monitor check summary and recommended action
- observed drift signals such as unknown Gemini-like ids, preview or premium
  model usage, and missing price metadata
- model catalog token prices and per-image prices for Gemini image models

This integration remains metadata-only. It does not call the gateway and does
not expose credentials, prompts, legal text, client identifiers, or raw model
outputs.

Run the targeted tests:

```powershell
cd app/backend
python -m pytest tests/test_model_price_refresh_monitor.py -q
```

Optional compile check:

```powershell
cd app/backend
python -m compileall services/model_price_refresh_monitor.py tests/test_model_price_refresh_monitor.py
```
