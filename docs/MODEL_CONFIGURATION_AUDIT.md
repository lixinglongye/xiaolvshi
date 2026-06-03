# Model Configuration Audit

The project now audits configured model roles before release.

## Purpose

The model catalog supports Gemini and NewAPI-compatible pass-through model names, but configured defaults still need review. A single `.env` mistake can turn high-volume classification, OCR, or fast preflight routes into premium calls. The configuration audit checks resolved model roles against cheap-first expectations.

## What It Checks

The audit evaluates:

- cheap text model role,
- fast task default,
- OCR task default,
- classification task default,
- balanced text model role,
- review task default,
- premium text model role,
- PDF task default.

For each role, it records:

- resolved model name,
- source environment variable,
- local catalog match,
- cost tier and max allowed tier,
- required and preferred capabilities,
- missing capabilities,
- over-budget status,
- pass/warn/fail result.

Unknown gateway model names are allowed for NewAPI compatibility, but they warn until the maintainer adds pricing and capability metadata to `model_catalog.py`.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes `model_configuration_audit`. The frontend `/model-ops` page shows the audit as a role table with status, model, cost tier, capability gaps, and reason.

## Release Readiness

`model-configuration-audit` is a required release-readiness check. Maintainers should run:

```bash
python -m pytest tests/test_model_configuration_audit.py tests/test_model_catalog.py tests/test_model_budget.py -q
```

## Safety

The audit only reads resolved model names and local catalog metadata. It does not read or expose API keys, prompts, documents, user identifiers, emails, passwords, or raw model output.

## Related files

- `app/backend/services/model_configuration_audit.py`
- `app/backend/services/model_catalog.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_model_configuration_audit.py`
- `app/backend/tests/test_model_catalog.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
