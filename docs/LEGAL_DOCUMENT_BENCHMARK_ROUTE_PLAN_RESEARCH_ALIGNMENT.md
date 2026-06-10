# Legal Document Benchmark Route Plan Research Alignment

This evidence slice maps local legal-document route-plan replay scenarios to
stored public research and official model-source anchors.

Routes:

- `GET /api/v1/maintenance/legal-review-benchmark/document-route-plan/research-alignment`
- `POST /api/v1/maintenance/legal-review-benchmark/document-route-plan/research-alignment`

The alignment uses metadata only:

- Google Gemini model documentation and pricing URLs anchor Flash-Lite/Flash
  route review before any cheap-first cost claim.
- FrugalGPT anchors selective escalation and premium route-down checks.
- LegalBench-RAG anchors grounded legal-opinion routing and citation/retrieval
  task separation.
- LexEval anchors zh-CN legal document task-family coverage for review,
  classification, and grounded opinion routes.

The service reuses the route-plan replay output. A failing replay blocks the
research-alignment claim instead of allowing a paper or official-source URL to
paper over routing drift.

`POST` can pass sanitized replay metadata under `route_plan_replay`, matching
the route-plan replay endpoint shape. Submitted scenario values are sanitized by
the replay service; raw rationale and sensitive values are not echoed.

This endpoint does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, public datasets, models, or the network. It does not download papers,
download benchmark data, execute benchmark runs, change defaults, shift traffic,
write configuration, or record approvals.

The response returns only source URLs, scenario ids, route metadata, alignment
rows, checks, counts, privacy boundaries, claim boundaries, and recommended
actions. It must not return public benchmark text, fixture snippets, prompts,
generated document text, model outputs, gateway responses, credentials, emails,
client identifiers, or submitted scenario rationale.

Validation:

```bash
cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_research_alignment.py -q
```

Full evidence gate:

```bash
cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_research_alignment.py tests/test_legal_document_benchmark_route_plan_replay.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression
```
