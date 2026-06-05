# ModelOps Gemini Cheap-First Coverage Gate

This gate is implemented as the backend metadata endpoint:

`GET /api/v1/aihub/models/gemini-cheap-first-coverage-gate`

It is release evidence for Gemini/NewAPI cheap-first routing coverage. It is not
a live model probe, public benchmark score, production traffic report, or
configuration writer.

## Coverage Dimensions

The gate keeps these dimensions reviewable:

- Gemini-like defaults: routine Gemini-compatible model ids should map to
  cheap-first defaults before balanced or premium options are considered.
- Cheap-first alignment: high-frequency review, OCR, classification, and light
  extraction paths should remain aligned with low-cost Gemini-compatible
  defaults unless a separate quality gate requires escalation.
- Premium exception: premium routing should stay explicit and reviewable for
  large PDF, deep reasoning, final review, or documented cheap-model failure
  cases.
- Unknown model: unrecognized Gemini-like or gateway-prefixed ids should be
  flagged for maintainer review instead of silently becoming defaults.
- Pricing compatibility: rows should expose price metadata coverage and
  unknown-price warnings without fetching external price pages.
- Lifecycle compatibility: rows should surface deprecated, preview, or
  lifecycle-risk labels before a model can be recommended as a default.
- Reasoning compatibility: rows should show whether reasoning-effort policy is
  compatible with the route and whether it implies premium review.
- Gateway compatibility: rows should mark OpenAI-compatible gateway fit,
  fallback needs, and compatibility gaps without calling a gateway.
- Claim/privacy boundary: rows should state that the gate is metadata-only and
  cannot support claims about live model quality, public benchmark scores, or
  production routing health.
- Agentic and grounded-research defaults: `auto-agentic` and
  `auto-grounded-research` should stay visible as cheap-first Gemini routes via
  `APP_AI_AGENTIC_MODEL` and `APP_AI_GROUNDED_RESEARCH_MODEL`, currently pinned
  to `gemini-3.1-flash-lite`.
- Template alignment: Settings defaults, `app/backend/.env.example`, the README
  env block, and `docs/AI_MODEL_STRATEGY.md` should remain aligned before
  maintainers change Gemini default models.

## Privacy Boundary

The gate must not call NewAPI, Gemini, OpenAI, Google, gateways, or the network.
It must not return raw prompts, payloads, model outputs, legal text,
credentials, headers, or account identifiers. Safe evidence is limited to model
ids, route labels, coverage status, warning ids, release-gate links, and
validation commands.

The companion default-template audit is exposed at:

`GET /api/v1/aihub/models/default-template-audit`

It compares checked-in templates and docs with Settings defaults only. It does
not read `.env`, process environment variables, gateway responses, prompts,
legal documents, or account data.

## Validation

Primary validation:

```bash
python -m pytest tests/test_model_default_template_audit.py tests/test_model_ops_readiness.py tests/test_model_catalog.py tests/test_modelops_gemini_cheap_first_coverage_gate.py -q
```

Supporting evidence validation:

```bash
python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
```
