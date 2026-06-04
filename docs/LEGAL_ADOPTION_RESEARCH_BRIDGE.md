# Legal Adoption Research Bridge

This bridge turns public legal-AI research and professional adoption signals into local product work without importing raw datasets, survey answers, client documents, model output, or credentials.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/adoption-research-bridge
```

The response includes:

- `method.input_sources`: public source metadata for LegalBench, FrugalGPT, RAGAS, CRAG, and professional AI governance/adoption reports.
- `actions`: research-backed product actions mapped to existing `user_need_ids`, `product_gap_ids`, `release_gate_links`, evidence paths, and low-resource validation commands.
- `implementation_queue`: the next reviewable actions, sorted by priority and cheap-first fit.
- `survey_intake_questions`: structured, privacy-safe prompts for future in-product user research.
- `release_guardrails`: claims that must remain blocked until stronger evidence exists.

## Current Mapping

The first queue item is `cheap-first-governed-review-loop`. It maps FrugalGPT-style cost-quality cascades and professional adoption governance signals to:

- `cheap-first-review-routing`
- `traceable-legal-review`
- `model-cost-ops`
- `contract-review`
- `gemini-newapi-model-selector`
- `gemini-newapi-selector-replay`

Other bridge actions cover legal RAG acceptance gates, synthetic legal task fixtures, governance-visible maintainer evidence, and a persona-survey-to-roadmap loop.

## Privacy Boundary

This is metadata-only evidence. It can store source titles, URLs, planning signals, local mappings, reason codes, evidence paths, validation commands, and survey question templates.

It must not store:

- raw public benchmark examples
- survey free text
- raw feedback
- client documents
- complete legal text
- prompts
- raw model outputs
- raw gateway payloads
- account emails
- credentials or API keys

The bridge is planning and release-evidence metadata only. It does not prove law-firm adoption, public benchmark scores, live NewAPI calls, survey results, productivity impact, or 24-hour maintenance completion.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_legal_adoption_research_bridge.py -q
python -m pytest tests/test_user_needs_radar.py tests/test_product_feature_gap_radar.py tests/test_legal_external_research_digest.py -q
```

Frontend review surface:

```powershell
npm run typecheck
```

## Related Files

- `app/backend/services/legal_adoption_research_bridge.py`
- `app/backend/tests/test_legal_adoption_research_bridge.py`
- `app/backend/routers/maintenance.py`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/USER_NEEDS_RADAR.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`
- `docs/LEGAL_EXTERNAL_RESEARCH_DIGEST.md`
- `docs/GEMINI_NEWAPI_MODEL_SELECTOR.md`
- `docs/GEMINI_NEWAPI_SELECTOR_REPLAY.md`
