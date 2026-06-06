# Case Export Readiness Download Gate

`CaseDetailPage` now routes case report, evidence catalog, and generated
document markdown downloads through `getMaintenanceCaseExportReadiness` before
calling the local `downloadText` helper.

The frontend builds a metadata-only readiness report with:

- `report_meta`: case id, document id, doc type, source action, selected-source
  validation status, and privacy flags.
- `risk_scoring`: risk level, unsupported fact count, and evidence metadata gap
  count.
- `citations`: source ids only.
- `evidence`: evidence ids, source ids, and boolean/review-status metadata.
- `release_decision`: ready or blocked status with reason codes.

If the gate returns `blocked`, the download is not started and the UI surfaces
`reason_codes` plus `recommended_actions`. `ready` downloads immediately, while
non-blocked review states can still download with a warning.

## Privacy Boundary

The readiness request must not include generated document content, report body,
evidence catalog markdown, parsed material text, file URLs, raw legal text, user
claims, PII, or credentials. The content is held locally and passed to
`downloadText` only after the readiness check returns a non-blocked status.

The frontend regression script enforces this with source checks around
`buildCaseExportReadinessPayload`, the readiness API call, and the number of
direct `downloadText(` references.

## Focused Checks

Run from `app/frontend`:

```powershell
npm run typecheck
npm run ui:regression
```

Run from `app/backend`:

```powershell
python -m pytest tests/test_case_export_readiness.py tests/test_frontend_ui_regression_gate.py -q
```
