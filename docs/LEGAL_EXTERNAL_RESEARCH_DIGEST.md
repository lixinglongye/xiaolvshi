# Legal External Research Digest

This digest maps public legal-AI, RAG, and cost-routing research signals into local engineering work for this project.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/external-research-digest
```

The endpoint returns:

- `signals`: external source metadata, checked signal, engineering takeaway, product area, validation target, and license/privacy gate.
- `implementation_queue`: the next engineering actions, with cheap-first routing first.
- `low_resource_validation`: small local commands that do not download datasets or call model gateways.
- `release_guardrails`: what must not be claimed or committed.

## Sources Tracked

- LegalBench: multi-task legal reasoning evaluation.
- CUAD: contract clause review and extraction dataset candidate.
- RAGAS: retrieval augmented generation evaluation metrics.
- CRAG: retrieval QA failure modes, factuality, and source availability.
- LegalBench-RAG: legal retrieval, citation grounding, unsupported-claim, and abstention task design.
- LexEval: Chinese legal cognition, reasoning, and generation benchmark planning.
- CaseGen: staged legal case document generation benchmark planning.
- FrugalGPT: cost-quality cascades and cheap-first escalation.

## Safety Policy

This digest stores source titles, URLs, planning signals, evidence paths, and validation commands only. It must not store:

- Public benchmark raw examples before license and attribution review.
- Real client documents or private legal matter facts.
- Raw model outputs or gateway JSON.
- API keys, account credentials, emails, or payment data.

## Related Files

- `app/backend/services/legal_external_research_digest.py`
- `app/backend/tests/test_legal_external_research_digest.py`
- `app/backend/services/legal_research_backlog.py`
- `app/backend/services/legal_public_benchmark_sampler.py`
- `app/backend/services/legal_fixture_result_archive.py`
- `docs/LEGAL_RESEARCH_BACKLOG.md`
- `docs/LEGAL_PUBLIC_BENCHMARK_SAMPLER.md`
- `docs/LEGAL_FIXTURE_RESULT_ARCHIVE.md`
