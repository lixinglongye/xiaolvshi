# Gemini/NewAPI Selector Replay Evidence

This document scopes the Gemini/NewAPI selector replay evidence endpoint. It is
a deterministic scenario replay surface for the model selector.
It is not a runtime model caller, gateway probe, or benchmark runner.

## Endpoint

```http
GET /api/v1/maintenance/gemini-newapi-selector-replay
POST /api/v1/maintenance/gemini-newapi-selector-replay
```

`GET` returns the fixed replay scenarios, expected cheap-first decisions,
premium-exception checks, warning checks, and repository evidence paths.

`POST` accepts maintainer-supplied selector replay metadata such as
scenario ids, task labels, model ids, canonical ids, cost tiers, decisions,
checks, warnings, and evidence paths. Submitted free-text rationale is replaced
with a generic metadata-only note and is not echoed. The endpoint must not
accept secrets, prompts, raw legal material, raw gateway responses, or raw model
output.

## Purpose

The replay evidence verifies whether the Gemini/NewAPI model selector still
chooses the expected cheap-first path for representative legal workflow
scenarios. It does this by replaying deterministic scenario inputs against the
selector contract and comparing metadata-level decisions.

The endpoint must not call NewAPI, Gemini, OpenAI, OpenRouter, Yibu, or any
other OpenAI-compatible gateway. It must not check live account access, model
availability, latency, quality, token usage, or billing. It only records whether
the selector decision matches the expected policy for each scenario.

## Required Scenario Coverage

The default replay set includes these scenario families:

- `fast`: cheap-first. The selector starts with the lowest qualified
  Flash-Lite or cheap tier candidate.
- `classification`: cheap-first. Classification and routing-like labels must
  not escalate to Flash or Pro without an explicit policy reason.
- `ocr`: cheap-first. OCR and extraction preflight routes start with the cheap
  candidate and keep high-volume scanned-page work out of premium defaults.
- `review`: balanced-after-precheck. The selector starts with a cheap precheck
  and allows a balanced Flash candidate only after the precheck indicates legal
  review depth, citation completeness, schema retry, or quality-gate need.
- `document_generation`: balanced-after-precheck. Drafting starts with a cheap
  precheck and allows a balanced candidate only for synthesis or formatting
  reliability needs.
- `large_pdf`: premium exception. Premium candidates such as Pro require an
  explicit exception, visible warning, and reviewer boundary.
- `final_review`: premium exception. Final legal review may recommend premium
  only as an exception, not as a silent default.
- `unknown_gemini_like_catalog_review`: unknown Gemini-like NewAPI ids are
  marked for catalog review until pricing, lifecycle, capability, and
  default-suitability metadata are added.
- `high_frequency_explicit_premium_block`: high-volume task labels with an
  explicit premium request are blocked or warned unless a premium exception is
  attached and justified.

Every replay result exposes:

- `id`
- `status`
- `scenario.id`
- `scenario.task`
- `scenario.explicit_model`
- `scenario.observed_models`
- `scenario.expected_decision`
- `scenario.max_cost_tier`
- `scenario.expected_selector_status`
- `actual.selected_model`
- `actual.canonical_model`
- `actual.cost_tier`
- `actual.decision`
- `actual.warnings`
- `checks`
- `recommended_action`

## Expected Decision Rules

Cheap-first scenarios pass only when the first accepted candidate is cheap and
known in the catalog. Balanced-after-precheck scenarios pass when the replay
shows a cheap precheck before a balanced recommendation. Premium-exception
scenarios pass only when the decision is explicitly labeled as an exception and
the replay includes a warning or check that prevents silent premium defaults.

Unknown Gemini-like catalog-review scenarios should not fail merely because the
model id is unknown. They should pass when the selector preserves the original
id, produces a canonical review placeholder or empty canonical id, marks the
catalog status as review-required, and avoids treating the model as a verified
cheap default.

High-frequency explicit premium scenarios should pass when the selector blocks
the premium request or emits a clear warning that the request conflicts with the
cheap-first policy for fast, routing, classification, OCR, triage, quote
extraction, batch summary, or similar high-volume labels.

## Metadata-Only Boundary

Selector replay records may store only:

- scenario ids,
- task labels,
- model ids,
- canonical ids,
- cost tiers,
- selector decisions,
- replay checks,
- warnings,
- evidence paths,
- validation command labels, and
- timestamps or opaque run ids.

Selector replay records must not store or return:

- API keys,
- NewAPI credentials,
- gateway credentials,
- base-url credentials or signed URLs,
- prompts,
- raw legal text,
- raw document excerpts,
- raw model outputs,
- raw gateway responses,
- raw OCR text,
- client names,
- user emails,
- mailbox content, or
- account passwords.

Evidence paths should point to repository files such as selector policy docs,
service tests, release-readiness docs, or sanitized fixture evidence. They
should not point to private client documents, local secret files, exported
gateway JSON, or copied model responses.

## Non-Claims

This endpoint must not be described as:

- a NewAPI/Gemini live probe,
- evidence that a gateway request succeeded,
- evidence that a selected model is available in a specific account,
- evidence that legal output quality is acceptable,
- evidence that prompts or raw outputs were reviewed,
- evidence that billing, latency, or token usage is correct, or
- proof that the 24-hour continuous maintenance window is complete.

It is selector regression evidence only: a reviewer-safe replay showing whether
the model selector still follows cheap-first, balanced-after-precheck,
catalog-review, and premium-exception policy for fixed scenarios.

## Validation

Keep validation focused and small:

```powershell
cd app/backend
python -m pytest tests/test_gemini_newapi_selector_replay.py -q
python -m pytest tests/test_gemini_newapi_model_selector.py tests/test_gemini_newapi_cheap_first_policy.py -q
```

The frontend maintenance panel uses the same GET evidence, so include the
existing lightweight checks:

```powershell
cd app/frontend
npm run typecheck
```

Useful repository checks while editing docs:

```powershell
rg -n "gemini-newapi-selector-replay|Selector Replay Evidence|high_frequency_explicit_premium_block" docs app
git diff --check -- docs
```

## Related Files

- `docs/GEMINI_NEWAPI_MODEL_SELECTOR.md`
- `docs/GEMINI_NEWAPI_CHEAP_FIRST_POLICY.md`
- `docs/MODEL_ROUTING_REPLAY.md`
- `docs/MODEL_FALLBACK_CHAINS.md`
- `docs/MODEL_ESCALATION_POLICY.md`
- `docs/RELEASE_READINESS.md`
- `docs/CONTINUOUS_UPDATE_LEDGER.md`
