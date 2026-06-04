# Route Telemetry Remediation Plan

The route telemetry remediation plan converts telemetry triage actions into
operator-reviewed cheap-first repair steps for Gemini/NewAPI routing.

## Purpose

`RouteTelemetryRemediationPlanService` consumes:

- `route_telemetry_triage`
- `default_optimization`

It produces:

- prioritized remediation steps,
- recommended `.env` assignments when a default should move back to a cheap
  capable Gemini model,
- manual-review flags,
- low-resource validation commands,
- release guardrails.

It never writes configuration and never calls NewAPI, Gemini, OpenAI, or any
gateway.

## Endpoints

```http
GET /api/v1/maintenance/route-telemetry-remediation
```

Returns the standalone remediation plan.

```http
GET /api/v1/aihub/models
```

The AIHub model-ops payload includes `route_telemetry_remediation`, and
`model_ops_readiness` includes a `route-telemetry-remediation` component.

The frontend `/model-ops` page renders the remediation plan after the telemetry
triage queue and before route guardrails.

## Release Checks

`route-telemetry-remediation-plan` is a required `model_ops` release-readiness
gate. It is required because triage actions must map to concrete reviewed steps
before maintainers change Gemini/NewAPI defaults.

Run:

```powershell
cd D:\小律师\app\backend
python -m pytest tests/test_route_telemetry_remediation_plan.py tests/test_route_telemetry_triage_queue.py tests/test_model_default_optimization.py -q
```

## Privacy Boundary

The plan uses metadata-only triage and default optimization rows. It must not
include prompts, legal text, client details, gateway credentials, headers,
request bodies, response bodies, raw payloads, emails, or raw model outputs.

## Related Files

- `app/backend/services/route_telemetry_remediation_plan.py`
- `app/backend/services/route_telemetry_triage_queue.py`
- `app/backend/services/model_default_optimization.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/routers/maintenance.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_route_telemetry_remediation_plan.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
