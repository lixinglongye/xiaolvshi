# Client Delivery Risk Checklist

## Purpose

`ClientDeliveryRiskChecklistService` defines a delivery gate for legal AI output before it reaches a client. The checklist focuses on product gaps that matter at release time: disclaimer visibility, lawyer review, citation and evidence support, client-readable uncertainty, audit records, and privacy minimization.

The service is intentionally deterministic. It does not call a model, read matter files, or download external data, so it can run on low-resource developer machines and in CI as a guardrail specification.

## Current Scope

- Pre-delivery checklist items with blocking, required, and advisory severity.
- Blocking items for citation or evidence support, lawyer review, and scope or assumption disclosure.
- Client-facing disclosures, including the internal i18n key `delivery.disclosure.not_legal_advice`.
- Separate lawyer and client perspectives so UI copy does not confuse professional review duties with client-readable risk disclosure.
- Audit record requirements for delivery decisions, reviewer status, citation coverage, disclosure acknowledgement, and redaction status.
- Low-resource validation commands for pytest and static scanning.
- Privacy notes requiring matter references and delivery logs to minimize personal data.

## Suggested API Endpoints

- `GET /api/v1/client-delivery/risk-checklist`: return the static checklist and disclosure copy for the frontend.
- `POST /api/v1/client-delivery/risk-checklist/evaluate`: evaluate a specific delivery package after citation audit, evidence audit, and lawyer review state are available.

The POST endpoint should block export, share, or send actions until all blocking items pass or an explicitly permitted lawyer override is recorded.

## Related Files

- `app/backend/services/client_delivery_risk_checklist.py`
- `app/backend/tests/test_client_delivery_risk_checklist.py`
- Future integration candidates: citation audit, evidence audit, release decision, delivery export, and matter audit-log services.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_client_delivery_risk_checklist.py -q
```

Optional static scan from the repository root:

```powershell
rg -n "sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}|(?i)(pwd|pass\\s*word|token)\\s*[:=]" app/backend/services/client_delivery_risk_checklist.py app/backend/tests/test_client_delivery_risk_checklist.py docs/CLIENT_DELIVERY_RISK_CHECKLIST.md
```

The static scan should return no matches.
