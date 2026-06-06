# Model Default Optimization

`model_default_optimization.py` turns the model capability matrix and monthly cost forecast into an operator action plan for NewAPI/Gemini defaults.

## What It Checks

- Compares each runtime default with the cheapest capable model from `model_capability_matrix.py`, which now uses `model_default_candidate_selector.py` for catalog-derived recommendations.
- Covers high-volume defaults: fast routing, classification, OCR, review, and PDF review.
- Covers explicit task models for grounded research, agentic planning, and image generation without changing env vars.
- Estimates monthly savings when switching a configurable default back to the recommended model.
- Marks premium PDF and media paths as manual-review exceptions.

## API Surface

`GET /api/v1/aihub/models` returns:

- `default_optimization.status`: `pass`, `warn`, or `fail`.
- `default_optimization.summary`: aligned tasks, required changes, manual-review count, and estimated savings.
- `default_optimization.recommendations`: task-level rows with current model, recommended model, env var, capabilities, savings, and reason.
- `default_optimization.recommended_actions`: copyable maintainer actions such as the current baseline `APP_AI_FAST_MODEL=gemini-2.5-flash-lite`, or a future lower-cost stable Flash-Lite candidate when the local catalog proves it.

The same payload is shown on the frontend `/model-ops` page.

## Release Use

Run this before model-routing releases:

```bash
cd app/backend
python -m pytest tests/test_model_default_optimization.py tests/test_model_capability_matrix.py -q
python -m pytest tests/test_model_default_candidate_selector.py tests/test_model_default_recommendation_snapshot.py -q
```

A `fail` status means a configurable default is over the task cost ceiling or lacks required capabilities. A `warn` status means pricing or catalog verification needs maintainer review before relying on that default.

## Safety

The optimization plan does not read prompts, documents, user identifiers, API keys, filenames, or raw model output. It only uses model IDs, catalog metadata, task requirements, and forecast assumptions.
