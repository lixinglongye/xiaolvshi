# Model Catalog Candidate Patch Plan

This document defines the metadata-only ModelOps plan for turning sanitized
observed Gemini-like gateway model ids into manual catalog patch candidates.

## Endpoint

```http
GET /api/v1/aihub/models/catalog-candidate-patch-plan
POST /api/v1/aihub/models/catalog-candidate-patch-plan
```

The endpoint is implemented by
`app/backend/services/model_catalog_candidate_patch_plan.py` and exposed through
`app/backend/routers/aihub.py`.

## Purpose

The observed Gemini intake queue can block unknown Gemini-like ids before they
become defaults. This plan adds the next review layer: it creates candidate
`ModelProfile` stubs and required metadata checks for maintainers without
editing `model_catalog.py`.

The plan can consume:

- sanitized `model_ids`
- sanitized OpenAI-compatible `models_response.data[*].id`
- sanitized Gemini native model-list wrappers such as `availableModels[*].name`
- sanitized `result.items[*].model_id` / `gateway_models_response.data[*].id`
- sanitized `gateway_probe_evaluation.model_rows[*].model`
- sanitized `observed_gemini_model_intake_queue.queue_items[*].raw_model`

All of these inputs pass through the shared Gemini/NewAPI observed-model
extractor used by the selector, variant matrix, alias matrix, and alias
capability coverage gates. The shared summary returns extractor version, source
field names, candidate/accepted/dropped counts, sensitive/invalid/total
rejection counts, and
`raw_payload_echoed: false` only. The patch plan uses `rejected_model_count`
for blocking, while `rejected_sensitive_count` and `rejected_invalid_count`
remain separate so maintainers can tell credential-like values from malformed
metadata.

## Boundaries

- Does not edit `model_catalog.py`.
- Does not write `.env`, templates, or runtime configuration.
- Does not call NewAPI, Gemini, OpenAI, Google, gateways, or the network.
- Does not shift traffic or approve default changes.
- Does not store raw payloads, prompts, legal text, model outputs, credentials,
  emails, Authorization headers, image URLs, or base64 data.

## Review Outputs

Each candidate row includes:

- observed model id
- proposed catalog id
- candidate patch action
- required catalog metadata checks
- proposed `ModelProfile` stub with unknown pricing and review-required status
- cheap-first/default-promotion boundary
- maintainer recommended action

Unknown Flash-Lite-like candidates remain blocked until official model-list,
pricing, lifecycle, capability, and gateway probe evidence are attached. Pro,
preview, and image candidates remain explicit-only unless maintainers approve a
narrow exception.

## Official Price And Status Gate

Candidate stubs whose official provider or gateway pricing, lifecycle status,
or availability has not been confirmed must remain `unpriced` and
`review-only`. Do not hard-code costs, claim cheap-first savings, or allow
default promotion until source-backed price, status, capability, and gateway
evidence are refreshed.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_model_catalog_candidate_patch_plan.py tests/test_model_ops_observed_gemini_model_intake_queue.py tests/test_model_gateway_probe_evaluation.py tests/test_model_ops_readiness.py -q
python -m pytest tests/test_gemini_newapi_observed_model_extraction.py tests/test_model_catalog_candidate_patch_plan.py -q
```

Run from `app/frontend`:

```powershell
npm run typecheck
npm run ui:regression
```
