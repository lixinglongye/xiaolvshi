# User Needs Radar

The project now has a deterministic user-needs radar for roadmap and release planning.

## Purpose

Legal AI improvements can easily become scattered feature work. The user-needs radar turns external research signals and local maintenance evidence into a ranked list of needs with:

- target user segments,
- pain points,
- product response,
- priority score,
- evidence paths,
- linked release gates,
- next actions.

## Endpoint

```http
GET /api/v1/maintenance/user-needs
```

The endpoint returns `status`, `method`, `summary`, `needs`, `roadmap`, and `maintenance_actions`.

Related legal-AI research planning is exposed at:

```http
GET /api/v1/maintenance/legal-review-benchmark/research-backlog
```

Use that endpoint when converting LegalBench, FrugalGPT, RAGAS, CRAG, or CUAD signals into concrete benchmark, routing, grounding, or UI tasks.

## Scoring

```text
priority_score = impact * confidence - effort * 4
```

Scores are bounded to `0-100` and grouped into:

- `high`: 50+
- `medium`: 35-49
- `low`: below 35

The score is a planning signal, not product analytics. It does not use private user documents or credentials.

## Research Signals

- LegalBench: legal AI evaluation should cover multiple legal reasoning task types instead of a single generic QA score.
- Stanford legal RAG hallucination evaluation: legal tools still need citation grounding checks, professional review, and hallucination-aware release gates.
- Internal feedback triage: support work should distinguish security, access, legal-output risk, pipeline failure, and usability.
- Local user research notes: target users need low-cost review, traceable evidence, missing facts, and lawyer-review escalation.
- Legal research backlog: paper and benchmark signals should become tested engineering work before they are used in public release claims.

## Current High-Priority Needs

- Traceable legal review output.
- Cheap-first model routing.
- Privacy-safe upload review.
- Robust document extraction.
- Prompt-injection resilience.

## Related files

- `app/backend/services/user_needs_radar.py`
- `app/backend/services/legal_research_backlog.py`
- `app/backend/routers/maintenance.py`
- `app/backend/tests/test_user_needs_radar.py`
- `app/backend/tests/test_legal_research_backlog.py`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/LEGAL_RESEARCH_BACKLOG.md`
