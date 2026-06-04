# Gemini/NewAPI Cheap-First Calibration

This document scopes the cheap-first calibration surface for Gemini/NewAPI
model operations. It joins existing selector replay, legal fixture smoke,
cost forecast, and cost guardrail metadata into a release-facing calibration
result.

It is not a live gateway probe, public benchmark score, billing report, or
proof of NewAPI account access.

## Endpoints

```http
GET /api/v1/aihub/models/cheap-first-calibration
POST /api/v1/aihub/models/cheap-first-calibration
```

`GET` returns the default local calibration built from synthetic legal fixture
metadata, selector replay scenarios, cost forecast profiles, and cost
guardrails.

`POST` accepts sanitized maintainer metadata for fixture-run reports and
selector replay. It must not echo raw prompts, legal text, gateway responses,
API keys, account emails, passwords, or raw model output.

The main ModelOps page also renders this calibration so maintainers can see
whether high-volume routes remain cheap-first, whether legal review stays
balanced-after-precheck, and which large-document paths remain premium
exceptions.

## Calibration Decisions

The service emits one row for each calibrated task family:

- `fast`: keep a lowest-tier cheap-first default.
- `classification`: keep a lowest-tier cheap-first default.
- `ocr`: keep a lowest-tier cheap-first default when fixture coverage passes.
- `review`: keep balanced Flash only after a cheap precheck.
- `document-generation`: keep balanced Flash only after a cheap precheck.
- `large-pdf`: require an operator-reviewed premium exception.

Each row includes the selected model metadata, cost tier, fixture score,
quality floor, release-gate links, reason codes, and a next action.

## Release Use

Calibration can support these release decisions:

- keep high-volume Gemini/NewAPI defaults on cheap models,
- hold a default change when fixture quality or guardrails fail,
- keep legal review on balanced-after-precheck instead of silent premium,
- require explicit premium exceptions for large documents, and
- attach metadata-only evidence to model-ops readiness.

Calibration must not be used as proof of:

- live NewAPI execution,
- model quality on public benchmarks,
- account billing status,
- production traffic coverage, or
- legal correctness for client matters.

## Privacy Boundary

The calibration payload may include only task ids, fixture ids, model ids,
canonical ids, cost tiers, scores, reason codes, release-gate ids, and
validation command labels.

It must not include:

- API keys or gateway credentials,
- user emails or account passwords,
- raw prompts,
- raw legal documents,
- raw OCR text,
- raw model outputs,
- raw gateway responses, or
- client-identifying matter facts.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_gemini_newapi_cheap_first_calibration.py tests/test_gemini_newapi_selector_replay.py tests/test_legal_fixture_run_report.py tests/test_model_cost_guardrails.py -q
```

Run from `app/frontend`:

```powershell
npm run typecheck
npm run build
```
