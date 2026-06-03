# Case Evidence Graph

The case evidence graph service defines a deterministic backend contract for connecting facts, evidence requirements, legal citations, and risk findings.

## Service

```python
from services.case_evidence_graph import CaseEvidenceGraphService

graph = CaseEvidenceGraphService().build_graph(report)
```

The service accepts already-normalized report fields and returns:

- `status`: `template`, `ready`, `review_recommended`, or `blocked`.
- `summary`: node, edge, risk, citation, evidence, pending-fact, and gap counts.
- `nodes`: risk, evidence requirement, citation, pending fact, and checklist nodes.
- `edges`: evidence-to-risk, citation-to-risk, and pending-fact-to-high-risk links.
- `gap_flags`: missing support, missing citation, missing appendix source, and blocking pending-fact flags.
- `delivery_phases`: backend contract and future case workbench UI phases.
- `validation_commands`: small local pytest commands.
- `privacy_note`: storage and release-safety guardrails.

## Why This Exists

The product needs more than a flat review report. Lawyers and legal operators need to see which facts, evidence, citations, and risks support each other. This service is the backend contract for that workflow before building a full graph UI.

## Safety Policy

Graph evidence should store normalized labels, IDs, statuses, and counts only. Do not commit or archive:

- Raw client documents.
- Full model outputs.
- Emails or private legal matter narratives.
- API keys, credentials, or authorization headers.

## Related Files

- `app/backend/services/case_evidence_graph.py`
- `app/backend/tests/test_case_evidence_graph.py`
- `app/backend/services/evidence_audit.py`
- `app/backend/services/citation_audit.py`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`
