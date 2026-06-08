# ModelOps Legal Fixture Evidence Handoff

`modelops-legal-fixture-evidence-handoff` is a metadata-only reviewer handoff
for low-resource legal fixture evidence. It is designed to make local fixture
results easier to review without moving raw model outputs, legal text, prompts,
or credentials into API responses, logs, docs, or git.

## Scope

- Joins local-run-review, cheap-first benchmark gate, default-promotion packet,
  and continuous-session-run-monitor summaries.
- Reports source status, ready/review/blocked/not-run counts, observed fixture
  counts, archived fixture counts, endpoint links, and release-readiness flags.
- Exposes the same packet through maintenance and AIHub ModelOps routes:
  `/api/v1/maintenance/legal-review-benchmark/evidence-handoff` and
  `/api/v1/aihub/models/legal-fixture-evidence-handoff`.

## Boundaries

The handoff must stay archive-safe. It does not return:

- `run_report_payload`, observations, raw gateway responses, choices, messages,
  prompts, headers, credentials, model outputs, output text, or raw legal text.
- NewAPI, Gemini, OpenAI, Google, gateway, network, configuration, default-change,
  or traffic-shift results.
- 24-hour completion claims, 100-update completion claims, GitHub push claims, or
  default-change claims.

If a caller submits sensitive or raw fields, the service counts raw field names
for reviewer visibility but does not echo field values.

## Validation

Run the low-resource validation slice from `app/backend`:

```bash
python -m pytest tests/test_modelops_legal_fixture_evidence_handoff.py tests/test_legal_fixture_local_run_review.py tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py tests/test_continuous_session_run_monitor.py tests/test_model_ops_readiness.py -q
```

This suite performs no provider calls and does not require public benchmark
downloads.
