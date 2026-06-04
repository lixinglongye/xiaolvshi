# Gemini/NewAPI Model Selector Evidence

This document scopes the upcoming Gemini/NewAPI model selector evidence endpoint.
It is a maintainer-facing selection audit and recommendation surface for
OpenAI-compatible Gemini model ids. It is not a runtime model caller.

## Endpoint

```http
GET /api/v1/maintenance/gemini-newapi-model-selector
POST /api/v1/maintenance/gemini-newapi-model-selector
```

`GET` should return the deterministic selector policy, default task candidate
chains, normalization examples, warnings, and repository evidence paths.

`POST` should accept maintainer-supplied metadata such as observed gateway model
ids, task labels, selected cost tiers, candidate chains, warning decisions, and
evidence paths. It should not accept secrets, prompts, raw legal material, or raw
gateway/model output.

## Purpose

The selector evidence helps maintainers answer these questions before changing
Gemini/NewAPI defaults:

- Does each observed OpenAI-compatible model id normalize to a known Gemini
  catalog id?
- Does the model fit the intended task label and cost tier?
- Does the candidate chain stay cheap-first before any premium exception?
- Are unknown Gemini-like ids clearly marked for catalog review instead of being
  treated as verified defaults?
- Which repository evidence paths support the recommendation?

The endpoint is metadata-only. It advises and audits model selection. It does
not call NewAPI, Gemini, OpenAI, OpenRouter, Yibu, or any other gateway. It also
does not prove that the 24-hour continuous maintenance goal is complete.

## Model Id Normalization

NewAPI and other OpenAI-compatible gateways may expose Gemini models with
different id shapes. The selector should normalize ids for catalog review while
preserving the original gateway id for operator visibility.

Recognized examples:

- Catalog id: `gemini-2.5-flash-lite`
- `models/` prefix: `models/gemini-2.5-flash-lite`
- `google/` prefix: `google/gemini-2.5-flash-lite`
- `google:` prefix: `google:gemini-2.5-flash-lite`

Normalization should produce:

- `original_model_id`: the exact id observed or supplied by the maintainer.
- `normalized_catalog_id`: the canonical Gemini catalog id when recognized.
- `prefix_type`: `catalog`, `models`, `google_slash`, `google_colon`, or
  `unknown_gemini_like`.
- `catalog_status`: `known`, `catalog_review`, or `unsupported`.
- `warnings`: review notes for unknown, preview, Pro, premium, deprecated, or
  over-budget ids.

Unknown ids that still look Gemini-like should remain explicit-only. They may be
passed through a gateway by a separate runtime caller, but this evidence endpoint
must mark them as `catalog_review` until pricing, lifecycle, capability, and
default-suitability metadata exist.

## Cheap-First Candidate Chains

The selector should emit task-specific candidate chains rather than a single
global default.

High-volume tasks start with Flash-Lite:

- `fast`: Flash-Lite first.
- `routing`: Flash-Lite first.
- `classification`: Flash-Lite first.
- `ocr`: Flash-Lite first.

Balanced legal production tasks use a cheap precheck before Flash:

- `review`: cheap precheck on Flash-Lite, then Flash when the precheck signals
  legal review depth, citation completeness, schema retry, or quality-gate need.
- `document_generation`: cheap precheck on Flash-Lite, then Flash for drafting
  steps that need stronger synthesis or formatting reliability.

Premium routes require an explicit exception:

- `large_pdf`: premium exception required before Pro or another premium tier.
- `final_review`: premium exception required before Pro or another premium tier.

The chain should expose:

- `task_label`
- `candidate_chain`
- `primary_candidate`
- `cheap_precheck_candidate`
- `fallback_candidates`
- `premium_exception_required`
- `max_allowed_cost_tier`
- `warnings`
- `evidence_paths`

Premium exception rows are allowed as recommendations only when the task and
warning metadata make the review boundary visible. They must not silently become
defaults for fast, routing, classification, OCR, triage, quote extraction, batch
summary, or other high-volume paths.

## Metadata-Only Boundary

Selector records may store:

- model ids,
- normalized catalog ids,
- task labels,
- cost tiers,
- candidate chains,
- warnings,
- evidence paths,
- validation command labels, and
- timestamps or opaque run ids.

Selector records must not store:

- API keys,
- NewAPI or gateway credentials,
- base-url credentials or signed URLs,
- prompts,
- raw legal text,
- raw document excerpts,
- raw model outputs,
- raw gateway responses,
- client names,
- user emails,
- mailbox content, or
- account passwords.

Evidence paths should point to repository files such as policy docs, service
tests, release-readiness docs, or sanitized fixture evidence. They should not
point to private client documents or local secret files.

## Non-Claims

This endpoint must not be described as:

- a NewAPI/Gemini live probe,
- evidence that a gateway request succeeded,
- evidence that a selected model is available in a specific account,
- evidence that a legal output is correct,
- storage for prompts or raw model output, or
- proof that the 24-hour continuous maintenance window is complete.

It is only selection evidence: a reviewable recommendation for how Gemini-like
model ids should map to cheap-first task chains and premium exception gates.

## Validation

When implementation exists, keep validation lightweight and targeted:

```powershell
cd app/backend
python -m pytest tests/test_gemini_newapi_model_selector.py -q
python -m pytest tests/test_gemini_newapi_cheap_first_policy.py tests/test_model_gateway_compatibility.py -q
```

Frontend wiring, if added later, should use the existing maintenance page
patterns and a targeted command:

```powershell
cd app/frontend
npm run typecheck
```

Useful repository checks while editing docs:

```powershell
rg -n "gemini-newapi-model-selector|Gemini/NewAPI Model Selector" docs app
git diff --check -- docs
```

## Related Files

- `docs/GEMINI_NEWAPI_CHEAP_FIRST_POLICY.md`
- `docs/MODEL_GATEWAY_COMPATIBILITY.md`
- `docs/MODEL_DEFAULT_RECOMMENDATION_SNAPSHOT.md`
- `docs/MODEL_FALLBACK_CHAINS.md`
- `docs/MODEL_ESCALATION_POLICY.md`
- `docs/RELEASE_READINESS.md`
- `docs/CONTINUOUS_UPDATE_LEDGER.md`
