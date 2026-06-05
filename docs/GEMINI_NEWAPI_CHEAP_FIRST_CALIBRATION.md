# Gemini/NewAPI Cheap-First Calibration

This document scopes the cheap-first calibration surface for Gemini/NewAPI
model operations. It joins existing selector replay, legal fixture smoke,
cost forecast, and cost guardrail metadata into a release-facing calibration
result.

It is not a live gateway probe, public benchmark score, billing report, or
proof of NewAPI account access.

The calibration also maps public legal benchmark and research experience to
local task families without importing any public dataset rows. Current
metadata-only mappings include:

- LegalBench for multi-task legal reasoning coverage.
- CUAD for contract clause extraction and contract review sampling.
- LexGLUE for legal classification and CaseHOLD-style routing signals.
- COLIEE for legal retrieval, entailment, and cited-support evaluation signals.
- DocLayNet for document layout and OCR/PDF precheck signals.

These mappings only influence local calibration policy: which task families
stay cheap-first, which require balanced-after-cheap-precheck, and which remain
operator-reviewed premium exceptions.

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

The same page includes a local evaluation form for sanitized calibration
payloads. The form posts only JSON metadata to
`POST /api/v1/aihub/models/cheap-first-calibration` and updates the on-page
result. It rejects obvious secrets, headers, prompts, emails, passwords, and
raw model output before submitting.

The backend repeats the safety check and returns only counts and field paths for
forbidden fields or secret-like values. It never echoes the raw value back to the
page.

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

Each row also carries `research_source_ids`, and the top-level payload includes
`external_research_mappings`. Those mappings contain only source IDs, public
links, task signals, local fixture IDs, policy impact, and import policy.

The ModelOps form template uses synthetic fixture labels and run metadata only.
It is intended for quick maintainer review of cheap-first decisions after a
small local fixture run, not for raw gateway responses.

## Release Use

Calibration can support these release decisions:

- keep high-volume Gemini/NewAPI defaults on cheap models,
- hold a default change when fixture quality or guardrails fail,
- keep legal review on balanced-after-precheck instead of silent premium,
- require explicit premium exceptions for large documents, and
- attach metadata-only evidence to model-ops readiness.

Calibration must not be used as proof of:

- live NewAPI execution,
- configuration writes,
- model quality on public benchmarks,
- account billing status,
- production traffic coverage, or
- legal correctness for client matters.

It also must not be used as proof that LegalBench, CUAD, LexGLUE, COLIEE,
DocLayNet, or any other public benchmark was downloaded or scored.

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
- copied public benchmark samples, labels, prompts, or outputs.

If a submitted payload contains forbidden field names such as headers,
authorization, password, prompt, email, secret, or a secret-like `sk-...` value,
the calibration status becomes `fail` and the summary records the blocked field
count without returning raw values.

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
