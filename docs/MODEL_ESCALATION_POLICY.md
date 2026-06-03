# Model Escalation Policy

The project now has a deterministic cheap-first escalation policy for Gemini/OpenAI-compatible model routing.

## Purpose

Routine legal workflow stages should not start on premium models. The escalation policy defines when a task can stay on the cheapest capable model, when it should verify with a balanced model, and when it may escalate to a premium exception path.

This follows the same cost-quality idea used by LLM cascade work such as FrugalGPT: start cheap, measure quality, and escalate only when deterministic signals justify the extra cost.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes:

- `budget_policy`
- `capability_matrix`
- `escalation_policy`
- `fallback_chains`
- `routing_replay`
- `models`
- `usage`

## Plans

Current escalation plans cover:

- `fast`: preflight, routing, triage, and light extraction.
- `ocr`: OCR and extraction assist.
- `review`: balanced legal review.
- `pdf`: large PDF and final review.
- `classification`: material classification.

## Decision Signals

Failure signals trigger escalation:

- `json_parse_error`
- `empty_output`
- `schema_missing_required`
- `citation_audit_fail`
- `evidence_audit_fail`
- `quality_gate_fail`
- `timeout`

Warning signals trigger verification:

- `low_confidence`
- `needs_context`
- `weak_citations`
- `missing_facts`
- `long_document`
- `ocr_uncertain`
- `unknown_model_price`

Hard stops prevent wasteful or unsafe retries:

- `privacy_high`
- `instruction_high`
- `extraction_quality_fail`

## Safety

The policy object contains only routing metadata. It does not store prompts, documents, credentials, file names, user emails, or raw model output.

## Replay coverage

`routing_replay` replays fixed legal workflow scenarios against this policy. It verifies that routine routes remain cheap-first, premium review routes still require operator review, and hard-stop signals do not select another model.

`fallback_chains` turns these escalation steps into per-task primary, verify, fallback, and premium-exception chains. This makes gateway or model availability changes easier to inspect before a maintainer changes defaults.

## Related files

- `app/backend/services/model_escalation_policy.py`
- `app/backend/services/model_fallback_chains.py`
- `app/backend/services/model_routing_replay.py`
- `app/backend/tests/test_model_escalation_policy.py`
- `app/backend/tests/test_model_fallback_chains.py`
- `app/backend/tests/test_model_routing_replay.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/pages/ModelOpsPage.tsx`
