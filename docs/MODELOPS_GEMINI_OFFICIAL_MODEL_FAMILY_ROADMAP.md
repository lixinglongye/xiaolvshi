# ModelOps Gemini Official Model Family Roadmap

`model_ops_gemini_official_model_family_roadmap.py` adds metadata-only evidence
for tracking official Gemini model family coverage against the local catalog and
cheap-first routing policy.

## Endpoint

```http
GET /api/v1/aihub/models/gemini-official-model-family-roadmap-evidence
```

The aggregate ModelOps payload also includes
`gemini_official_model_family_roadmap_evidence`, and `model_ops_readiness`
treats it as a required configuration signal.

## Official Source Anchors

- Gemini models: `https://ai.google.dev/gemini-api/docs/models`
- Gemini pricing: `https://ai.google.dev/gemini-api/docs/pricing`
- Gemini OpenAI compatibility: `https://ai.google.dev/gemini-api/docs/openai`

These links are review anchors only. They do not claim that local catalog rows
are current until a maintainer refreshes local pricing, lifecycle, capability,
and gateway notes.

## What It Tracks

- Gemini 2.5 text and multimodal rows as covered cheap-first text/vision
  defaults through stable Flash-Lite, Flash, and Pro catalog entries.
- Gemini 3 text, agentic, and grounding rows as review-required because preview
  and partially reviewed boundaries still need maintainer confirmation.
- Gemini image generation and editing rows as explicit media routes, not
  high-frequency text defaults.
- Gemini Live/audio, embedding, and TTS families as roadmap gaps until catalog,
  pricing, request-policy, and route boundaries exist.
- High-frequency tasks that should remain on stable Flash-Lite defaults before
  any premium or preview default promotion is considered.

## What It Returns

- `official_source_rows`: official source review anchors and tracked signals.
- `family_rows`: official family label, local catalog rows, coverage status,
  route policy, missing capabilities, and maintainer action.
- `roadmap_items`: per-family priority, owner, status, and next action.
- `cheap_first_evidence_rows`: high-frequency task defaults and cheap-first
  eligibility.
- `checks`: coverage, cheap-first default, roadmap-gap, review-boundary, and
  no-live/default-change-claim checks.
- `privacy_boundary` and `claim_boundary`: explicit no-call, no-write,
  no-secret, no-payload, and no-all-supported boundaries.

## Non-Claims

This evidence does not call Gemini, Google, NewAPI, OpenAI, gateways, app AI
endpoints, models, or the network. It does not write configuration, change
defaults, execute live gateway requests, prove pricing accuracy, claim
production quality, or claim that every official Gemini model is supported.

It also does not return request bodies, response bodies, headers, prompts, raw
payloads, raw legal text, model outputs, emails, credentials, or user
identifiers.

## Validation

```bash
python -m pytest tests/test_model_ops_gemini_official_model_family_roadmap.py tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```

## Related Files

- `app/backend/services/model_ops_gemini_official_model_family_roadmap.py`
- `app/backend/tests/test_model_ops_gemini_official_model_family_roadmap.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/frontend_ui_regression_gate.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
