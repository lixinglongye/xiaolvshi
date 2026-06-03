# Client Delivery Transparency Policy

This backend policy defines the local gates that must pass before a legal document package becomes client-deliverable. It covers client confirmation, version differences, risk notice visibility, delivery audit records, and post-delivery task tracking.

## Service

- File: `app/backend/services/client_delivery_transparency_policy.py`
- Class: `ClientDeliveryTransparencyPolicyService`
- Entry point: `build_policy(payload: dict | None = None) -> dict`
- Runtime behavior: deterministic local metadata evaluation only; no network access, no model call, no OCR run, and no credential lookup.

## Output Contract

The service returns:

- `status`: `pass`, `warn`, or `fail`
- `summary`: aggregate counts and release decision fields
- `checks`: detailed check results for each policy area
- `delivery_gates`: release effects for each check (`allow`, `warn`, or `block`)
- `recommended_actions`: concrete remediation steps grouped by failed or warning check
- `privacy_note`: data-minimization rule for integration work
- `validation_commands`: low-resource commands for local verification

## Required Payload Areas

Use redacted IDs and metadata only. Do not send raw client narratives or full document text into this policy layer.

```json
{
  "artifact": {
    "current_version_id": "version-002",
    "previous_version_id": "version-001"
  },
  "client_confirmation": {
    "status": "confirmed",
    "confirmed_at": "2026-06-04T08:00:00Z",
    "confirmed_version_id": "version-002"
  },
  "version_diff": {
    "summary_available": true,
    "client_visible": true,
    "diff_acknowledged": true,
    "material_change_count": 2
  },
  "risk_notice": {
    "present": true,
    "client_visible": true,
    "acknowledged": true,
    "risk_level": "medium"
  },
  "delivery_record": {
    "record_id": "delivery-001",
    "delivery_channel": "client_portal",
    "prepared_at": "2026-06-04T08:10:00Z",
    "package_version_id": "version-002",
    "accountable_actor": "lawyer-001"
  },
  "follow_up_tasks": [
    {
      "task_id": "task-001",
      "owner_role": "lawyer",
      "due_at": "2026-06-05",
      "status": "open"
    }
  ]
}
```

## Gate Semantics

- `client-confirmation`: blocks delivery unless the client confirmed the exact current version.
- `version-diff`: blocks delivery when the version difference summary is missing, hidden from the client, or unacknowledged after material changes.
- `risk-notice`: blocks delivery unless material risks, scope limits, and client acknowledgement are present.
- `delivery-record`: blocks delivery unless package version, channel, timestamp, and accountable actor metadata are ready for audit.
- `follow-up-tasks`: warns when task tracking is absent; fails only when the payload explicitly marks follow-up as required.

## Privacy

The policy output must not echo client names, contact details, full file paths, raw document text, private notes, or credentials. Integrations should store sensitive matter data in protected case storage and pass only stable IDs, booleans, counts, timestamps, and role labels to this service.

## Validation

From `app/backend`:

```powershell
python -m pytest tests/test_client_delivery_transparency_policy.py -q
python -m compileall services/client_delivery_transparency_policy.py
```
