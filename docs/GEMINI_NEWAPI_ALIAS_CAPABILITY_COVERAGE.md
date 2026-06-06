# Gemini/NewAPI Alias Capability Coverage

This release gate expands local Gemini catalog entries across OpenAI-compatible
gateway aliases and checks whether each alias still resolves to known capability,
task, lifecycle, and cost metadata.

## Scope

- Covers canonical Gemini ids plus `models/`, `google/`, `google:`, `yibu/`,
  `yibu:`, `yibuapi/`, `newapi/`, `openrouter/google/`,
  `openai/gemini/`, and `publishers/google/models/` shapes.
- Normalizes Gemini native action and lifecycle suffixes such as
  `:generateContent`, `:streamGenerateContent`, `@latest`, and `@stable`.
- Uses the shared Gemini/NewAPI observed-model extractor for submitted
  `observed_models`, OpenAI-compatible `/models` wrappers such as
  `models_response.data`, Gemini native wrappers such as `availableModels`,
  gateway probe rows, and observed-model intake queue rows.
- Reports task coverage, high-frequency cheap-first eligibility,
  balanced-after-precheck eligibility, premium/media review boundaries, and
  unknown observed model review states.

## Safety Boundary

- Metadata only: no NewAPI, Gemini, OpenAI, Google, gateway, or network calls.
- No configuration writes, traffic shifts, default changes, approval records, or
  environment mutation.
- Observed model ids are sanitized; secrets, authorization values, emails,
  prompts, legal text, raw payloads, and model outputs are rejected or omitted.
- Source summaries include extractor version, source field names, counts,
  supported model-id fields, `rejected_sensitive_count`,
  `rejected_invalid_count`, `rejected_model_count`, and
  `raw_payload_echoed: false`; they do not return headers, request bodies,
  response bodies, prompts, legal text, or model output.
- Capability review blocks on the total rejected model count, while sensitive
  and invalid counts stay separate so maintainers can distinguish credential
  leakage from malformed model metadata.
- Unknown Gemini-like aliases remain review-only until catalog, price,
  lifecycle, capability, and gateway compatibility evidence is added.

## Validation

Run:

```bash
python -m pytest tests/test_gemini_newapi_observed_model_extraction.py tests/test_gemini_model_variant_matrix.py tests/test_gemini_newapi_model_selector.py tests/test_gemini_newapi_model_alias_matrix.py tests/test_gemini_newapi_alias_capability_coverage.py tests/test_model_catalog_candidate_patch_plan.py -q
python -m pytest tests/test_gemini_newapi_alias_capability_coverage.py tests/test_gemini_newapi_model_alias_matrix.py tests/test_gemini_newapi_model_selector.py tests/test_model_catalog.py tests/test_model_ops_readiness.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```

The ModelOps page displays this packet between the Gemini variant matrix and the
Gemini cheap-first coverage gate.
