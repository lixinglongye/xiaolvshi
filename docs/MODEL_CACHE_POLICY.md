# Model Cache Policy

`model_cache_policy.py` describes where repeated Gemini/NewAPI model work can use hash-only cache metadata to reduce cost without storing prompts or user documents.

## Policy

The cache policy is intentionally metadata-only. It does not implement a cache store and does not persist model responses. It defines:

- cache eligibility by task,
- TTL by task,
- expected hit rate for cost planning,
- hash-only cache key material,
- privacy boundaries for sensitive legal inputs,
- estimated monthly savings from the cost forecast.

## Current Task Rules

- `fast`: hash exact normalized request metadata for short-lived preflight and routing repeats.
- `classification`: hash material fingerprints and schema version for deterministic high-volume classification.
- `ocr`: hash page image fingerprints and OCR prompt version for repeated extraction fallback.
- `review`: cache only redacted rubric patterns, not full user facts.
- `pdf`: disabled by default because source documents may contain sensitive facts.

## API Surface

`GET /api/v1/aihub/models` returns `cache_policy`:

- `status`: `pass`, `warn`, or `fail`.
- `summary`: enabled rules, estimated monthly savings, warnings, and blocking checks.
- `rules`: task-level cache mode, TTL, expected hit rate, key material, privacy boundary, and estimated savings.

The frontend `/model-ops` page shows the same policy near request cost bounds.

## Release Check

```bash
cd app/backend
python -m pytest tests/test_model_cache_policy.py tests/test_model_ops_readiness.py -q
```

A `fail` means an enabled cache rule is not deterministic enough for exact-result reuse. A `warn` means cost forecast data is missing and savings cannot be estimated.

## Safety

Allowed cache metadata is limited to task labels, canonical model ids, schema or prompt-version ids, deterministic hashes, and aggregate counters. The policy explicitly disallows storing raw prompts, documents, page images, file names, users, emails, API keys, or raw model output.
