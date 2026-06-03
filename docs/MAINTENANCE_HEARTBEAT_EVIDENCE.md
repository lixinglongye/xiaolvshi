# Maintenance Heartbeat Evidence

This service defines a privacy-safe evidence export for long-running maintenance
windows. It helps reviewers inspect timestamped work without storing account
credentials, raw legal documents, prompts, or raw model outputs.

## Endpoint

```http
GET /api/v1/maintenance/maintenance-heartbeat-evidence
POST /api/v1/maintenance/maintenance-heartbeat-evidence
```

The default `GET` response is a template and remains `collecting`. It does not
claim the 24-hour work target is complete.

`POST` accepts explicit heartbeat metadata:

```json
[
  {
    "event_type": "commit",
    "timestamp": "2026-06-04T00:00:00Z",
    "commit_hash": "1234567",
    "evidence_paths": ["app/backend/services/example.py"]
  }
]
```

## Event Types

- `commit`: repository-backed code, test, or documentation work.
- `test`: focused validation such as pytest, typecheck, lint, build, or secret scan.
- `push`: remote GitHub evidence was published.
- `review`: release readiness, maintenance evidence, or safety review action.

## Output

`MaintenanceHeartbeatEvidenceService().build_evidence(events)` returns:

- `status`
- `summary`
- `event_type_schema`
- `heartbeat_records`
- `gap_analysis`
- `recommended_actions`
- `privacy_note`
- `validation_commands`

The service computes `verified_continuous_hours` from valid event timestamps and
requires all four event types before the evidence is marked `ready_for_review`.

## Privacy Boundary

Records may include only event ids, event types, timestamps, commit hashes,
validation labels, and repository paths. Do not include API keys, account
credentials, emails, raw client documents, prompts, raw model responses, or
private legal matter text.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_maintenance_heartbeat_evidence.py -q
```
