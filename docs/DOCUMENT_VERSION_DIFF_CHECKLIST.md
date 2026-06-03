# Document Version Diff Checklist

`DocumentVersionDiffChecklistService` defines client-safe version diff metadata
for generated legal document delivery.

## Scope

The checklist validates:

- current and previous version ids
- sanitized change summary
- changed section names
- reviewer role
- client-visible summary
- optional risk change summary
- optional source support status

It intentionally stores metadata only. It must not include raw document text,
client contact details, account credentials, API keys, passwords, or internal
privileged notes.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_document_version_diff_checklist.py -q
python -m compileall services/document_version_diff_checklist.py tests/test_document_version_diff_checklist.py
```
