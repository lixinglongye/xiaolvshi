# Legal RAG Evaluation

This project now has a deterministic evaluation policy for legal retrieval-augmented generation runs.

The policy is based on four practical observations from recent legal RAG work:

- Legal RAG Bench emphasizes end-to-end legal RAG evaluation and reports that retrieval quality is a primary driver of correctness and groundedness: https://arxiv.org/abs/2603.01710
- The Grounded in Law anti-hallucination pipeline uses staged retrieval, citation constraints, and post-generation verification for legal answers: https://aclanthology.org/2026.propor-2.9.pdf
- Legal citation verification products such as CiteShield focus on making every cited legal authority independently reviewable: https://www.citeshield.com/
- LegalCiteBench studies citation recovery, citation verification, and case matching for legal language models: https://arxiv.org/abs/2605.10186
- RAG evaluation tooling increasingly includes privacy checks and document-level evaluation artifacts: https://www.rageval.dev/

## Endpoints

```http
GET /api/v1/legal-knowledge/rag-evaluation-policy
POST /api/v1/legal-knowledge/rag-evaluation
GET /api/v1/legal-knowledge/grounding-quick-audit-policy
POST /api/v1/legal-knowledge/grounding-quick-audit
```

`/grounding-quick-audit` combines this RAG score with citation and evidence audits. It can infer conservative RAG metrics from a deep-review report, but inferred metrics remain a warning until an explicit `rag_run` is supplied.

## Evaluation inputs

- `expected_source_ids`: legal sources that should be retrieved.
- `retrieved_source_ids`: legal sources retrieved by the system.
- `answer_citation_source_ids`: sources cited by the generated answer.
- `verified_claim_count`: generated legal claims verified against source text.
- `total_claim_count`: total generated legal claims checked.
- `unsupported_claims`: unsupported legal claims, each with severity.
- `stale_source_ids`: retrieved sources that need refresh.
- `pii_findings`: privacy findings, each with severity.

## Metrics

- Retrieval recall: expected legal-source recovery.
- Citation precision: cited sources must come from retrieved sources.
- Claim verification: generated legal claims must be verified against source text.
- Source freshness: stale legal sources reduce readiness.
- Privacy safety: critical PII findings block release.

The service does not call an AI model. It scores explicit evaluation artifacts so maintainers can plug it into CI, manual review, or future benchmark runs.

For release checks that need one combined signal across legal sources, risk citations, evidence plans, and RAG metrics, use [LEGAL_GROUNDING_QUICK_AUDIT.md](LEGAL_GROUNDING_QUICK_AUDIT.md).
