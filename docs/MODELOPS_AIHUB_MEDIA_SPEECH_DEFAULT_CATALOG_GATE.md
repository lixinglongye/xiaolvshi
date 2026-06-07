# ModelOps AIHub Media/Speech Default Catalog Gate

`modelops-aihub-media-speech-default-catalog-gate` is required metadata-only
release evidence for AIHub media and speech defaults.

## Endpoint

```http
GET /api/v1/aihub/models/aihub-media-speech-default-catalog-gate
POST /api/v1/aihub/models/aihub-media-speech-default-catalog-gate
```

The aggregate `GET /api/v1/aihub/models` payload also exposes the same evidence
under `aihub_media_speech_default_catalog_gate`.

## What It Reviews

The gate reviews current and future AIHub media/speech default coverage:

- image generation and editing
- video generation
- speech generation and TTS
- audio transcription and understanding
- future Live native audio
- future embedding and RAG indexing

It links those rows to the AIHub endpoint route coverage gate, local catalog
status, explicit media/speech budget modes, official Gemini/Veo/TTS source
anchors, default release actions, review items, and privacy/claim boundaries.

## Release Policy

This gate is required release evidence because media and speech defaults can be
easy to over-claim. Non-catalog defaults, missing pricing, preview lifecycle
models, and future-route families stay explicit-review only until source-backed
catalog, pricing, lifecycle, gateway behavior, and route policy evidence is
attached.

The gate does not change defaults, write configuration, shift traffic, call
providers, call gateways, call app AI endpoints, call models, or use the
network.

## Non-Claims

This evidence does not claim:

- all media or speech models are supported
- official catalog refresh is complete
- Live audio or embedding routes exist
- pricing is accurate for every default or candidate
- a gateway request was executed
- any AIHub default was changed

It also does not return request bodies, response bodies, headers, prompts, raw
payloads, audio, transcripts, legal text, model outputs, gateway responses,
credentials, emails, or user identifiers.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_model_ops_aihub_media_speech_default_catalog_gate.py tests/test_model_ops_aihub_endpoint_route_coverage_gate.py tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```
