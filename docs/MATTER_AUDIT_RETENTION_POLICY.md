# Matter Audit Retention Policy

This service defines privacy-minimized audit logging rules for legal matter workflows.

## Purpose

The case workspace, AI review flow, lawyer review, export flow, and sensitive-operation controls need consistent audit records. `MatterAuditRetentionPolicyService.build_policy()` keeps required fields, forbidden fields, retention buckets, and reviewer value explicit before those workflows are wired to persistent storage.

## Future Endpoints

```http
GET /api/v1/maintenance/matter-audit-retention-policy
POST /api/v1/maintenance/matter-audit-retention-policy
```

The `GET` endpoint returns the policy template. The `POST` endpoint can evaluate sample event metadata and return blocking issues.

## Events Covered

- `case_access_changed`
- `ai_review_started`
- `lawyer_review_decision`
- `client_delivery_exported`
- `sensitive_operation_denied`

## Safety Policy

Audit records should store actor IDs, matter IDs, version IDs, decisions, timestamps, redaction status, route IDs, and source references. They should not duplicate raw legal text, full attachments, direct contact details, raw model prompts, raw model outputs, API keys, or login credentials.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_matter_audit_retention_policy.py -q
```

## Related Files

- `app/backend/services/matter_audit_retention_policy.py`
- `app/backend/tests/test_matter_audit_retention_policy.py`
- `app/backend/services/case_team_access_policy.py`
- `app/backend/services/client_delivery_risk_checklist.py`
- `app/backend/services/legal_document_export_readiness.py`
