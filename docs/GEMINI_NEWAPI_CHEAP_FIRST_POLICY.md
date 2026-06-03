# Gemini/NewAPI Cheap-First Model Selection Policy

## Purpose

`GeminiNewapiCheapFirstPolicyService` defines a backend-only policy for using
Gemini models through NewAPI or another OpenAI-compatible gateway. The policy
keeps high-volume legal workflow tasks on the lowest capable Gemini family and
requires review before unknown, preview, Pro, or premium models become defaults.

The service is intentionally metadata-only. It does not read gateway credentials,
does not persist prompts, and does not store uploaded legal documents.

## Service

File:

- `app/backend/services/gemini_newapi_cheap_first_policy.py`

Main entry point:

- `GeminiNewapiCheapFirstPolicyService.build_policy(observed_models=None)`

The returned payload includes:

- `supported_gemini_model_families`
- `newapi_openai_compatible_prefix_compatibility`
- `default_model_recommendations`
- `cheap_first_task_ladder`
- `unknown_gemini_like_model_handling`
- `forbidden_default_rules`
- `observed_model_review`
- `validation_commands`
- `privacy_note`

## Supported Gemini Families

The policy groups Gemini models into practical routing families:

- `gemini-flash-lite`: default for high-volume fast, routing, classification,
  OCR, triage, quote extraction, and batch summary tasks.
- `gemini-flash`: balanced legal review, drafting, and extraction retry.
- `gemini-pro`: premium exception path for complex reasoning and final review.
- `gemini-image`: explicit media route only.

Flash-Lite is the only family that is allowed as a high-frequency default.

## NewAPI And OpenAI-Compatible Prefixes

The policy treats the model field as OpenAI-compatible gateway metadata. It
supports common Gemini shapes for catalog review:

- `gemini-2.5-flash-lite`
- `models/gemini-2.5-flash-lite`
- `google/gemini-2.5-flash-lite`
- `google:gemini-2.5-flash-lite`

Gateway ids that look Gemini-like but are not in the local catalog are not
blocked outright. They are marked `catalog_review` with warning severity and
remain explicit-only until tier, stability, and default suitability are checked.

## Cheap-First Defaults

High-volume tasks must default to:

- `fast`: `gemini-2.5-flash-lite`
- `classification`: `gemini-2.5-flash-lite`
- `ocr`: `gemini-2.5-flash-lite`

Balanced legal work can use:

- `review`: `gemini-2.5-flash`
- `document_generation`: `gemini-2.5-flash`

Premium routes are exception-only:

- `large_pdf_final_review`: `gemini-2.5-pro`

## Forbidden Defaults

The policy rejects high-frequency defaults when a model name or catalog profile
indicates:

- `pro`
- `preview`
- `premium`
- unknown Gemini-like model

These models can still be used as explicit experiments, quality escalations, or
final review exceptions after review. They must not become defaults for fast,
classification, OCR, routing, triage, batch summary, or quote extraction.

## Low-Resource Validation

Run the targeted test:

```powershell
cd D:\小律师\app\backend
python -m pytest tests/test_gemini_newapi_cheap_first_policy.py -q
```

Optional compile check:

```powershell
cd D:\小律师\app\backend
python -m compileall services/gemini_newapi_cheap_first_policy.py tests/test_gemini_newapi_cheap_first_policy.py
```

## Privacy Boundary

This policy payload should contain only routing metadata and catalog labels. Do
not place raw prompts, legal documents, client contact identifiers, or gateway
credentials inside the returned policy.
