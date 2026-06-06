# Deep Review Export Readiness Gate

`GET /api/v1/deep-review/reports/{report_id}/export/{file_format}` now checks
metadata-only case export readiness before serializing a stored deep-review
report into `pdf`, `doc`, `md`, or `json`.

The route validates the requested format first, prepares the stored report for
display, then builds a privacy-safe readiness payload with:

- `report_meta`: selected-source validation status and report metadata.
- `risk_scoring`: deterministic risk score metadata.
- `citations`: citation audit counts and source reviewability counts.
- `evidence`: evidence audit coverage and blocking pending-fact counts.
- `release_decision`: delivery status and blocker state.

If the gate is not `ready`, the route returns HTTP `409` before generating any
download body. The response includes only `status`, `reason_codes`,
`missing_sections`, selected-source validation status, recommended actions, and
the privacy boundary.

## Privacy Boundary

Blocked export responses must not include stored report JSON, raw document
text, client emails, generated legal analysis, file URLs, download content, or
credentials. The exported file is serialized only after readiness passes.

## Focused Checks

Run from `app/backend`:

```powershell
python -m pytest tests/test_deep_review_export_gate.py tests/test_case_export_readiness.py -q
```
