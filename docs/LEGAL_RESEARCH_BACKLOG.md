# Legal Research Backlog

The legal research backlog converts external legal-AI papers and benchmark sources into concrete engineering work for this project. It is designed for maintainer planning, release evidence, and cheap-first model-routing decisions.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/research-backlog
```

The endpoint returns:

- `input_sources`: primary papers and benchmark candidates used as planning signals.
- `backlog`: prioritized engineering items with workstream, linked user needs, release gates, and evidence paths.
- `workstream_plan`: grouped actions for model ops, benchmark design, retrieval quality, and frontend review.
- `next_iteration_queue`: the next highest-signal work items.
- `maintenance_actions`: how to use the backlog in release planning.

## Research Sources

- LegalBench: legal reasoning evaluation should cover multiple legal task families, not a single generic score.
- FrugalGPT: cost-quality cascades support trying cheaper models first and escalating selectively.
- RAGAS: retrieval-augmented generation needs faithfulness, answer relevance, and context relevance metrics.
- CRAG: retrieval QA evaluation should include factuality, source availability, and retrieval failure modes.
- CUAD: contract review evaluation benefits from clause-level issue spotting and extraction tasks, after license review.

## Current High-Priority Items

- `cheap-first-cascade-evaluation`: keep Gemini/NewAPI fixture runs cheap-first and escalate only selected failures.
- `legal-task-coverage-map`: keep each fixture tied to legal task family, expected route, signals, and output tasks.
- `rag-grounding-metric-gates`: map RAGAS/CRAG signals to citation, evidence, grounding, and unsupported-claim gates.

## Low-Resource Policy

The backlog is planning metadata only. It does not download public datasets or call any gateway. Research-inspired changes should be validated with:

```bash
python -m pytest tests/test_legal_research_backlog.py tests/test_legal_fixture_local_run_review.py -q
```

For small machines, use `/local-run-package?fixture_limit=1` followed by `/local-run-review` before running broader fixture suites.

## Safety

- Do not commit public benchmark raw examples until license, attribution, and privacy review pass.
- Do not put API keys, real client documents, emails, or raw model outputs into backlog items.
- Do not claim production legal accuracy from this backlog. It is a planning and maintenance artifact.

## Related Files

- `app/backend/services/legal_research_backlog.py`
- `app/backend/tests/test_legal_research_backlog.py`
- `app/backend/routers/maintenance.py`
- `app/backend/services/legal_fixture_evidence_bundle.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/maintenance_evidence.py`
- `docs/LEGAL_REVIEW_BENCHMARK.md`
- `docs/LEGAL_BENCHMARK_FIXTURES.md`
- `docs/USER_NEEDS_RADAR.md`
- `docs/USER_RESEARCH_AND_MAINTENANCE.md`
