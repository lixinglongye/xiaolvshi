# OSS Maintenance Evidence

This project includes a small maintenance evidence endpoint for open-source support applications and reviewer-facing project summaries.

## Endpoint

```http
GET /api/v1/maintenance/oss-evidence?language=en
GET /api/v1/maintenance/oss-evidence?language=zh
```

The response includes:

- `project`: repository URL and project domain.
- `maintainer_role`: the role claimed for this repository.
- `evidence_score`: a deterministic score based on reviewable maintenance signals.
- `signals`: code, test, documentation, and release-management evidence paths.
- `responsibilities`: ongoing maintainer duties.
- `release_management`: current release-readiness controls.
- `application_guardrails`: claims that must be manually verified before submitting a support form.
- `form_answer`: a concise English or Chinese paragraph suitable for support application fields.

## Why this exists

Support applications often ask for proof of active maintenance, review duties, release management, and ecosystem importance. The service intentionally ties each claim to repository artifacts so the maintainer can avoid unverifiable statements.

It is safe to say this repository has active development, reviewability controls, tests, documentation, and release-readiness logic. It is not safe to claim external adoption, third-party pull-request volume, issue triage volume, or production releases unless those records exist publicly in GitHub.

## Evidence categories

- Model operations: model catalog, configuration audit, default optimization, gateway compatibility, model-ops readiness, budget policy, task inference, runtime routing, reasoning effort policy, request parameter policy, request cost bounds, cache policy, route telemetry, route guardrails, callsite audit, fallback chains, routing replay, usage-safe telemetry.
- Quality control: deep-review quality gates, legal-review benchmark cases, cheap-first legal fixture prompt packs, safe gateway request manifests, laptop-safe fixture run plans, cheap-first fixture run reports, lightweight synthetic legal document fixtures, and fixture-driven prompt/schema improvement planning.
- Review operations: citation and evidence audits.
- Release management: risk scoring and unified release decision.
- Product visibility: frontend report page, report mapping, and API types.
- Maintenance planning: user research and maintenance notes.

## Related files

- `app/backend/services/maintenance_evidence.py`
- `app/backend/routers/maintenance.py`
- `app/backend/tests/test_maintenance_evidence.py`
- `docs/USER_RESEARCH_AND_MAINTENANCE.md`
