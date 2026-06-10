# Legal Document Benchmark Route Plan Execution Claim Gate

`legal-document-benchmark-route-plan-execution-claim-gate` is a
metadata-only release/support claim gate for the legal-document route-plan
execution evidence chain.

Endpoints:

- `GET /api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-claim-gate`
- `POST /api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-claim-gate`

The gate evaluates proposed wording against the execution review packet and
returns only hashes, detected claim types, reason codes, release actions, and
safe policy metadata. It never echoes the original claim text.

## What It Checks

- Metadata-only route-plan execution wording is backed by a ready review
  packet.
- Public benchmark score claims are blocked.
- Live provider execution claims are blocked.
- Maintainer, release, or approval-recorded claims are blocked.
- Default-model, production-default, rollout, and traffic-shift claims are
  blocked.
- Production-quality, lawyer-grade, real-client-document, or guaranteed legal
  accuracy claims are blocked.
- Secret-like values, emails, authorization values, and other sensitive
  material are dropped and never echoed.

## Allowed Claim Shape

Only narrow repository evidence wording can be allowed when the review packet is
ready:

> Repository evidence includes a metadata-only legal-document route-plan
> execution review packet for sanitized manual observation metadata after
> readiness, archive, handoff, cheap-first, and low-resource checks.

If the review packet is not ready, even metadata-only wording is held for
review.

## Boundaries

This service does not:

- Echo raw claim text.
- Execute benchmark runs.
- Call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or
  the network.
- Write release records, archive files, configuration, defaults, or traffic
  shifts.
- Record maintainer approval.
- Claim public benchmark scores, production quality, release approval, default
  changes, traffic shifts, or live provider execution.
- Return public benchmark text, raw legal text, fixture snippets, prompts,
  request bodies, response bodies, headers, generated text, model outputs,
  gateway responses, emails, identifiers, or credentials.

## Validation

```bash
cd app/backend
python -m pytest tests/test_legal_document_benchmark_route_plan_execution_claim_gate.py -q
```
