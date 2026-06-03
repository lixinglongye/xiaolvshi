# Model Request Policy

The project now applies task-level generation parameter policy before text requests are sent to an OpenAI-compatible gateway.

## Purpose

Cheap-first routing should also keep generation budgets bounded. A high-volume classification or OCR call should not inherit the same output budget as a deep legal review. The request policy chooses effective `temperature` and `max_tokens` after task inference and runtime model routing.

## Defaults

| Task | Temperature | Max tokens | Rationale |
| --- | ---: | ---: | --- |
| `fast` | `0.1` | `1024` | Keep preflight and routing output short by default. |
| `classification` | `0.0` | `768` | Produce compact deterministic labels or JSON. |
| `ocr` | `0.0` | `2048` | Keep OCR deterministic while allowing page text output. |
| `review` | `0.2` | `4096` | Preserve enough room for legal analysis without verbose defaults. |
| `pdf` | `0.0` | `8192` | Premium-exception path with deterministic output to reduce retry risk. |

Explicit caller values are respected up to task ceilings. Review and PDF paths allow larger explicit budgets because some stages need long structured reports. JSON `response_format` lowers the temperature ceiling to reduce parse failures and retries.

## API

`GenTxtRequest` accepts optional:

```json
{
  "temperature": 0.2,
  "max_tokens": 4096
}
```

When omitted, the backend uses task policy defaults. Non-streaming `GenTxtResponse` includes `request_policy` with the effective temperature, max token budget, adjustment flags, response format mode, and rationale.

## Model Ops

```http
GET /api/v1/aihub/models
```

The response includes `request_policy`, and the frontend `/model-ops` page shows the effective defaults for each task.

## Release Readiness

`model-request-policy` is a required release-readiness check. Maintainers should run:

```bash
python -m pytest tests/test_model_request_policy.py tests/test_aihub_runtime_routing.py -q
```

## Safety

The policy only evaluates task names and numeric generation parameters. It does not store prompts, uploaded documents, file names, API keys, passwords, emails, user identifiers, or raw model output.

## Related files

- `app/backend/services/model_request_policy.py`
- `app/backend/services/aihub.py`
- `app/backend/schemas/aihub.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_model_request_policy.py`
- `app/backend/tests/test_aihub_runtime_routing.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
