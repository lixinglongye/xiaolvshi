# Legal RAG Abstention Escalation Gate

`GET /api/v1/maintenance/legal-rag-abstention-escalation-gate`

This maintenance endpoint is release evidence for Legal RAG answer routing. It
joins local hallucination triage metadata, authority/citation gate metadata, and
cheap-first model escalation policy metadata into deterministic answer,
warning, abstention, clarification, lawyer-review, and premium-exception rows.

## Gate Meaning

- `answer`: selected source and citation metadata are sufficient for a guarded
  answer. This allows answer delivery, subject to the normal downstream release
  decision and citation display rules.
- `answer_with_warning`: answer delivery may continue only with visible caveats
  when the metadata shows conflicts, weaker evidence, or reviewer-visible risk.
- `abstain`: the system must withhold the legal answer until grounding is
  repaired. This blocks client delivery for that row.
- `ask_clarification`: the system must ask for missing fact, source,
  jurisdiction, or retrieval metadata before attempting a legal answer. This is
  not a premium-model shortcut.
- `lawyer_review`: a lawyer or maintainer must review authority, freshness,
  citation, or legal-reasoning risk before answer release.
- `premium_exception`: cheaper checks failed and a premium review path is only
  allowed after explicit operator approval. It is not a default route and does
  not override abstention, lawyer review, or missing-source blockers.

## Linkage

The gate is a join layer, not a new source of truth:

- It links hallucination labels from
  `legal-rag-hallucination-triage-gate` to answer modes, release actions,
  reviewer actions, and blocker status.
- It links authority and citation rows from
  `legal-rag-authority-citation-gate` to citation grounding, authority status,
  freshness, and selected-source readiness.
- It links model policy metadata from `model-escalation-policy` only to record
  cheap-first or premium-exception boundaries. It does not run model selection
  or call a gateway.

The gate can support reviewer visibility on the maintenance evidence page and
release-readiness summaries. It does not prove live Legal RAG accuracy,
hallucination-free behavior, public benchmark scores, or client-deliverable
legal advice.

## Cheap-First And Premium Exception Boundary

Cheap-first is the default for metadata checks and non-premium answer modes:

- `answer`, `answer_with_warning`, and `ask_clarification` stay in cheap-first
  metadata review.
- `lawyer_review` stays a human review gate before any answer release.
- `premium_exception` is an explicit exception path that requires operator
  approval and still keeps gateway calls outside this evidence endpoint.
- `abstain` is a stop condition, not an escalation to a more expensive model.

Premium models must not be used to bypass missing citations, hallucinated
authority, stale law, jurisdiction mismatch, insufficient retrieved context, or
lawyer-review blockers.

## Metadata Boundary

Evidence is metadata-only. The endpoint may return mode labels, case ids,
failure labels, linked gate ids, linked authority row ids, score bands, boolean
privacy flags, release actions, and validation commands.

It must not:

- call NewAPI, Gemini, OpenAI, model gateways, crawlers, or external networks;
- download benchmark datasets;
- save or return prompts;
- save or return raw retrieved context;
- save or return raw legal text;
- save or return fixture original questions;
- save or return dangerous or unsafe fixture answers;
- save or return model outputs, gateway payloads, credentials, account data,
  client material, or emails.

## Evidence Paths

- `app/backend/services/legal_rag_abstention_escalation_gate.py`
- `app/backend/tests/test_legal_rag_abstention_escalation_gate.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/maintenance_evidence.py`
- `app/backend/services/frontend_ui_regression_gate.py`
- `docs/LEGAL_RAG_ABSTENTION_ESCALATION_GATE.md`

## Validation

```bash
python -m pytest tests/test_legal_rag_abstention_escalation_gate.py tests/test_legal_rag_hallucination_triage_gate.py tests/test_legal_rag_authority_citation_gate.py -q
python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
```
