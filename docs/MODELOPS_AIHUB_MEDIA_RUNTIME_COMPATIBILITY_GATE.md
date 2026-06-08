# ModelOps AIHub Media Runtime Compatibility Gate

`modelops-aihub-media-runtime-compatibility-gate` is required metadata-only
release evidence for AIHub media runtime endpoint shapes.

## Endpoint

```http
GET /api/v1/aihub/models/aihub-media-runtime-compatibility-gate
POST /api/v1/aihub/models/aihub-media-runtime-compatibility-gate
```

The aggregate `GET /api/v1/aihub/models` payload also exposes the same evidence
under `aihub_media_runtime_compatibility_gate`.

## What It Reviews

The gate separates current AIHub runtime code paths from native Gemini, Veo,
TTS, and Live route requirements:

- `genvideo` currently uses `client.videos.create` and
  `client.videos.retrieve`.
- `genaudio` currently uses `client.audio.speech.create`.
- `transcribe` currently uses `client.audio.transcriptions.create`.
- Live audio has no AIHub session route yet.

Those endpoint shapes can work only when a gateway emulates the same
OpenAI-compatible methods. Native Veo video generation, Gemini TTS,
Gemini audio understanding, and Gemini Live audio can require different
request shapes, polling or session behavior, response modalities, and output
extraction.

## Release Policy

Veo, Gemini TTS, Gemini audio-understanding, and Live audio promotion remains
review-only until maintainers attach runtime evidence for the exact gateway
shape or a native adapter. The gate does not change defaults, write
configuration, shift traffic, call providers, call gateways, call app AI
endpoints, call models, or use the network.

## Non-Claims

This evidence does not claim:

- native Gemini media routes are implemented
- Veo works through the current `videos.create` path
- Gemini TTS works through the current `audio.speech.create` path
- Gemini audio understanding works through the current transcription path
- Live audio routes exist
- any AIHub default was changed

It also does not return request bodies, response bodies, headers, prompts, raw
payloads, audio, transcripts, legal text, model outputs, gateway responses,
credentials, emails, or user identifiers.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_model_ops_aihub_media_runtime_compatibility_gate.py tests/test_model_ops_aihub_media_speech_default_catalog_gate.py tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```
