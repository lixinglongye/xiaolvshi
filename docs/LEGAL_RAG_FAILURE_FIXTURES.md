# Legal RAG Failure Fixtures

This module adds a small deterministic fixture suite for legal RAG failure checks on low-resource local machines.

## Purpose

`LegalRagFailureFixturesService` defines synthetic RAG failure cases that can be evaluated without external model calls, downloaded datasets, or real client documents. The suite targets failures that are common in legal retrieval workflows:

- Missing citations for legal conclusions
- Stale regulations when a newer authority is retrieved
- Jurisdiction mismatches between matter facts and cited rules
- Evidence that does not support the answer conclusion
- Hallucinated article numbers or citations
- Conflicting retrieved facts that were not escalated

## Output Shape

`build_suite()` returns:

- `fixture_cases`: six small synthetic legal RAG failure scenarios.
- `failure_taxonomy`: deterministic failure labels, severities, signals, and reviewer actions.
- `evaluation_rules`: local-only scoring rules for structured observations.
- `privacy_note`: fixture maintenance constraints.
- `validation_commands`: the pytest command for this module.

`evaluate_observations(observations)` accepts structured observations keyed by fixture case ID:

```python
{
    "rag-missing-citation-small": {
        "detected_failure_labels": ["missing_citation"],
        "evidence_signals": ["legal_conclusion_without_source_id"],
        "recommended_actions": ["block_final_answer", "ask_for_citation"],
        "released_to_user": False,
    }
}
```

The evaluator scores failure-label coverage, evidence-signal coverage, remediation-action coverage, and whether unsafe release was blocked. It uses deterministic set coverage only.

## Privacy And Resource Policy

- No external model calls.
- No network access.
- No public or private legal dataset downloads.
- No real client facts, names, addresses, phone numbers, emails, identity numbers, source documents, model transcripts, or API keys.
- Keep fixtures short enough for fast laptop pytest runs.

## Validation

Run from the repository root:

```powershell
cd app/backend
python -m pytest tests/test_legal_rag_failure_fixtures.py -q
```
