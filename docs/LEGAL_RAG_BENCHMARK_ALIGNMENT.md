# Legal RAG Benchmark Alignment

`legal-rag-benchmark-alignment` adds a metadata-only scorecard for mapping
public Legal RAG benchmark signals to local release evidence.

Endpoint:

`GET /api/v1/maintenance/legal-rag-benchmark-alignment`

The scorecard joins existing local gates:

- `legal-rag-retrieval-diagnostics-gate`
- `legal-rag-abstention-escalation-gate`
- `legal-review-benchmark/public-sampler`
- `legal-review-benchmark/fixture-crosswalk`

It maps LegalBench-RAG, CRAG, RAGAS, and Legal RAG Bench style signals into
local dimensions for source coverage, citation grounding, corrective retrieval,
abstention, Chinese legal-document transfer, contract clause grounding, and
cheap-first Gemini/NewAPI default boundaries.

The endpoint does not run models, call NewAPI/Gemini, call gateways, access the
network, download public datasets, or return public benchmark text, raw queries,
retrieved context, raw legal text, prompts, model outputs, credentials, or
gateway payloads.

The response includes:

- `summary`: dimension counts, blockers, linked gate counts, and privacy flags.
- `alignment_rows`: per-dimension coverage scores, missing targets, missing
  fixtures, public-source sampling states, release actions, and cheap-first
  policy.
- `benchmark_dimensions`: the static local mapping contract.
- `research_basis`: source ids and URLs only.
- `claim_boundary`: allowed and forbidden claims.
- `privacy_boundary`: explicit no-raw-content and no-network flags.

Validation:

```bash
python -m pytest tests/test_legal_rag_benchmark_alignment.py tests/test_legal_rag_retrieval_diagnostics_gate.py tests/test_legal_benchmark_fixture_crosswalk.py -q
cd app/frontend && npm run typecheck && npm run ui:regression
```
