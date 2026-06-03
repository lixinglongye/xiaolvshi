# Evidence Exhibit Package Policy

`EvidenceExhibitPackagePolicyService` defines the backend contract for evidence catalogs and attachment delivery packages.

The service is deterministic. It checks exhibit metadata already held by the product layer and does not open uploaded files, call models, run OCR, or inspect original document text.

## Scope

- Evidence catalog metadata schema.
- Exhibit and attachment numbering.
- Page anchors for catalog-to-attachment jumps.
- Proof purpose mapping to facts, disputes, claims, defenses, or risk items.
- Source anchors back to intake records or evidence graph nodes.
- Authenticity, relevance, and legality review gates.
- Export manifest requirements for delivery packages.

## Service Contract

Suggested call:

```python
from services.evidence_exhibit_package_policy import EvidenceExhibitPackagePolicyService

policy = EvidenceExhibitPackagePolicyService().build_policy(
    {
        "exhibits": [
            {
                "exhibit_number": "E-001",
                "attachment_number": "A-001",
                "title": "Signed contract excerpt",
                "source_anchor": "source:upload-001",
                "page_anchor": "pages 1-3",
                "proof_purpose": "Proves contract formation and delivery obligation.",
                "authenticity_review": "passed",
                "relevance_review": "passed",
                "legality_review": "passed",
            }
        ]
    }
)
```

Returned top-level sections:

- `status`: `template`, `blocked`, or `ready`.
- `exhibit_metadata_schema`: required and optional exhibit fields.
- `package_checks`: export readiness checks with linked blocking issue IDs.
- `blocking_issues`: deterministic blockers with reviewer actions.
- `review_actions`: actions grouped by failed package check.
- `export_manifest_fields`: manifest fields required for package export.
- `low_resource_validation_commands`: local checks that do not need large fixtures.
- `privacy_notes`: metadata-only handling rules.

## Blocking Rules

The package is blocked when any exhibit lacks:

- `exhibit_number`
- `attachment_number`
- `source_anchor`
- `page_anchor`
- `proof_purpose`
- `authenticity_review`
- `relevance_review`
- `legality_review`

The package is also blocked when exhibit numbers are duplicated or when authenticity, relevance, or legality review is failed or still pending.

## Export Manifest

The export manifest should include:

- Package ID, case ID, package version, and generated time.
- Final review status and reviewer ID.
- Exhibit count and ordered exhibit number list.
- Attachment file IDs, names, order, and checksums.
- Page anchor index.
- Proof purpose index.
- Authenticity, relevance, and legality review summary.
- Confidentiality map, delivery channel, and retention rule ID.

## Low-Resource Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_evidence_exhibit_package_policy.py -q
```

Optional repository check:

```powershell
git diff --check -- app/backend/services/evidence_exhibit_package_policy.py app/backend/tests/test_evidence_exhibit_package_policy.py docs/EVIDENCE_EXHIBIT_PACKAGE_POLICY.md
```

## Privacy Notes

Keep this policy metadata-only. Use exhibit IDs, package IDs, page ranges, review states, checksums, and redacted labels. Do not store private party details, full local file paths, original document text, or model output in policy payloads.
