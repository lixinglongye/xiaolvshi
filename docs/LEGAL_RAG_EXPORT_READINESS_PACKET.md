# Legal RAG Export Readiness Packet

`legal-rag-export-readiness-packet` adds a maintenance review packet for Legal
RAG report export. It joins three existing gates into one reviewer-facing
payload:

- selected-source citation validation,
- deep-review selected-source binding,
- case/deep-review export readiness.

Endpoint:

```text
POST /api/v1/maintenance/legal-rag/export-readiness-packet
```

The packet returns status, release action, check rows, reason codes, linked
release gates, recommended actions, and validation commands. It never returns
the bound report object.

## Privacy Boundary

The service is metadata-only. It does not return raw reports, legal text,
document text, user claims, PII, prompts, model outputs, credentials, NewAPI
payloads, Gemini payloads, gateway responses, or network results.

It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, or
the network. It only evaluates explicit report metadata supplied to the
maintenance route.

## Validation

```text
python -m pytest tests/test_legal_rag_export_readiness_packet.py tests/test_deep_review_selected_source_binding.py tests/test_case_export_readiness.py -q
python -m pytest tests/test_deep_review_export_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py -q
cd app/frontend && npm run typecheck && npm run ui:regression
```
