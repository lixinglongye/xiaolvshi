# Model Ops Readiness

The project now aggregates model-operation checks into one release-oriented readiness result.

## Purpose

Model operations now include configuration audit, default template alignment, default optimization, default recommendation snapshots, gateway compatibility, gateway connection profiling, gateway health planning, optional gateway probe evaluation evidence, Gemini lifecycle policy, Gemini catalog source audit, observed Gemini intake, observed gateway model fit evidence, runtime explicit model fit evidence, candidate patch planning, runtime routing, reasoning effort policy, request parameter policy, gateway request compatibility, Gemini cheap-first route preflight, AIHub endpoint route coverage, AIHub media/speech default catalog review, AIHub media runtime compatibility review, user-need Gemini route coverage, request cost bounds, cache policy, route telemetry, route telemetry repository, route telemetry operations summary, route telemetry triage queue, route telemetry remediation plan, route guardrails, cheap-first route quality budgets, model failure upgrade budgets, cheap-first escalation budgets, callsite audit, capability matrix, routing replay, fallback chains, escalation policy, cost forecast, cost guardrails, Gemini/NewAPI cheap-first calibration, price refresh monitoring, ModelOps load performance budgets, release decision packets, default-change queues, canary packets, maintainer execution evidence, and low-resource legal micro benchmark preflight evidence. Reviewing each signal separately is error-prone before a release.

`model_ops_readiness` combines these signals into one pass/warn/fail result.
`cheap_first_release_decision` consumes this readiness result downstream, along
with focused Gemini/cheap-first signals, but it is not counted as another
readiness component.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes:

```json
{
  "model_ops_readiness": {
    "status": "warn",
    "release_recommendation": "maintainer_review_required",
    "summary": {
      "component_count": 61,
      "required_component_count": 60,
      "optional_component_count": 1,
      "pass_count": 41,
      "warn_count": 20,
      "fail_count": 0,
      "required_warning_count": 19,
      "optional_review_count": 1,
      "required_failure_count": 0,
      "optional_failure_count": 0,
      "blocking_count": 0,
      "warning_count": 20,
      "warning_drilldown_count": 20,
      "p0_warning_count": 0,
      "p1_warning_count": 19,
      "p2_warning_count": 1
    },
    "warning_category_counts": {},
    "warning_drilldown": []
  }
}
```

The frontend `/model-ops` page shows the readiness summary near the top of the page, followed by the warning drilldown, warning category counts, and component table.

## Warning Drilldown

`warning_drilldown` expands every non-passing readiness component into an actionable row:

- `severity`: `p0_blocking_required`, `p1_required_review`, or `p2_optional_review`.
- `priority`: numeric sort key used to put blocking and high-risk warning rows first.
- `warning_category`: one of `manual_evidence_gap`, `canary_evidence_gap`, `catalog_pricing_review`, `default_recommendation_review`, `runtime_telemetry_review`, `routing_quality_review`, `cost_guardrail_review`, `release_evidence_review`, `configuration_review`, `resilience_review`, or `general_review`.
- `next_action`: the maintainer action to resolve or accept the warning.
- `validation_hint`: the local pytest command most relevant to the warning class.
- `privacy_boundary`: explicit metadata-only flags showing that the row does not include prompts, raw payloads, model outputs, credentials, gateway responses, or network/model calls.

`warning_category_counts` mirrors the drilldown rows as aggregate counts for UI filtering and release review. The drilldown never calls NewAPI, Gemini, OpenAI, Google, gateways, or the network; it only classifies existing readiness metadata already present in the `/api/v1/aihub/models` response.

## Components

The readiness service checks:

- model configuration audit,
- default optimization plan,
- default recommendation snapshot,
- gateway compatibility,
- gateway connection profile,
- gateway health plan,
- Gemini variant matrix,
- observed Gemini coverage gap queue,
- observed gateway model fit matrix,
- runtime explicit model fit gate,
- Gemini catalog source audit,
- gateway probe evaluation,
- Gemini lifecycle policy,
- budget policy,
- capability matrix,
- runtime router,
- reasoning policy,
- request policy,
- gateway request compatibility gate,
- Gemini cheap-first route preflight,
- AIHub endpoint route coverage gate,
- AIHub media/speech default catalog gate,
- AIHub media runtime compatibility gate,
- user-need Gemini route coverage,
- request cost bounds,
- cache policy,
- callsite audit,
- route telemetry,
- route telemetry repository,
- route telemetry operations summary,
- route telemetry triage queue,
- route telemetry remediation plan,
- route guardrails,
- cheap-first route quality budget,
- model failure upgrade budget,
- legal micro benchmark preflight,
- cheap-first escalation budget,
- routing replay,
- fallback chains,
- escalation policy,
- cost forecast,
- cost guardrails,
- Gemini/NewAPI cheap-first calibration,
- Gemini/NewAPI price refresh monitor,
- ModelOps performance budget.

Any required `fail` status blocks model-ops readiness. Any `warn` status requires maintainer review before treating the model stack as release-ready. The summary separates `required_warning_count`, `required_failure_count`, and `optional_review_count` so manual evidence does not look like a required gate failure. `gateway-probe-evaluation` is optional manual evidence: missing or `not_run` results warn but do not block, while supplied failing probe evidence is surfaced as a warning with its underlying blocker IDs. After a maintainer posts sanitized gateway probe results, `/api/v1/aihub/models` uses the latest in-process sanitized snapshot for this optional component; rejected payloads only contribute a minimal safe failure snapshot.

`default-recommendation-snapshot` is required evidence for cheap-first default
review. It binds `default_recommendation_snapshot` into the readiness
component table, exposes role-level `blocking_check_ids` and
`warning_check_ids`, and classifies non-passing rows as
`default_recommendation_review`. Maintainers must resolve blocked default roles
or observed Gemini catalog-review models before changing environment defaults.
The snapshot remains metadata-only: model names, cost tiers, capabilities, and
role ids are allowed; prompts, raw payloads, model outputs, legal text,
gateway responses, credentials, emails, and user identifiers are not returned.

`model-ops-performance-budget` is required evidence for the local operations UI. It checks that the heavyweight `/api/v1/aihub/models` payload has a short backend cache, the frontend has a request timeout and abort path, and the page does not repeat the cheap-first calibration request on first load.
Submitted performance observations are also bound back into aggregate review:
`POST /api/v1/aihub/models/performance-budget` recomputes readiness and the
cheap-first release decision with the sanitized observation result, and later
in-process `/api/v1/aihub/models` payloads use that latest sanitized result.
Slow rows become review warnings or blockers without storing raw payloads.

`route-quality-budget` is required evidence for cheap-first model routing. It checks that each task has deterministic quality gates, a cheap-start model where appropriate, and a visible review action when a runtime default lacks the required task capabilities.

`cheap-first-escalation-budget` is required evidence for cheap-first cascade cost control. It checks aggregate failure, verification, escalation, premium escalation, operator review, and wasted escalation spend rates before a cheap Gemini/NewAPI default can be promoted.

`model-failure-upgrade-budget` is required evidence for single-request failure handling. It checks sanitized failure metadata, attempt budget, hard-stop signals, incremental cost, task budget tier, premium quota, and operator approval before any retry-up or premium exception is allowed.

`legal-micro-benchmark-preflight` is required metadata-only evidence for the smallest cheap-first legal benchmark run. It selects fixture ids, document case ids, fact-consistency case ids, a serial run order, cheap-first cost estimates, and follow-up gate endpoints without calling models or gateways, writing configuration, shifting traffic, or returning request bodies, messages, prompts, legal text, model output, gateway responses, credentials, or emails.

`gateway-request-compatibility-gate` is required metadata-only evidence for
OpenAI-compatible Gemini/NewAPI request shapes. It checks task default model
selection, gateway-prefixed model normalization, request parameter caps, JSON
response-format needs, reasoning-effort policy, and cheap-first cost bounds
without calling models or gateways, writing configuration, shifting traffic, or
returning headers, request bodies, prompts, raw legal text, model output,
payloads, emails, or credentials.

`gemini-cheap-first-route-preflight` is required metadata-only evidence for the
Gemini route plan before default changes. It joins official source refresh
notes, local task defaults, the Gemini variant matrix, alias capability
coverage, and the cheap-first coverage gate so high-frequency tasks stay on
stable Flash-Lite defaults while preview, premium, media, unknown, unpriced, or
retired variants remain review/explicit-only. It does not call NewAPI, Gemini,
OpenAI, Google, gateways, app AI endpoints, or the network, write
configuration, shift traffic, or return request/response bodies, headers,
prompts, raw payloads, legal text, model output, gateway responses,
credentials, emails, or user identifiers.

`observed-gateway-model-fit-matrix` is required metadata-only evidence for
sanitized OpenAI-compatible gateway inventory fit. It maps observed model-list
IDs to canonical Gemini catalog metadata, task capabilities, lowest-cost
observed candidates, missing task coverage, and review-only Pro, preview,
media, unknown, external, or unpriced boundaries before any route or default
change. It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, or the network, write configuration, shift traffic, or
return request/response bodies, headers, prompts, raw payloads, legal text,
model output, gateway responses, credentials, emails, or user identifiers.

`runtime-explicit-model-fit-gate` is required metadata-only evidence for
explicit runtime model requests. It runs sanitized task/model scenarios through
the local runtime router to surface unknown gateway guards, reviewed gateway
pass-through exceptions, explicit over-budget exceptions, local downgrades,
cheap-first alignment, and observed gateway fit review states before
maintainers rely on a route. It does not call providers, gateways, app AI
endpoints, models, or the network, write configuration, change defaults, shift
traffic, or return request/response bodies, headers, messages, prompts, raw
payloads, legal text, model output, gateway responses, credentials, emails, or
user identifiers.

`aihub-endpoint-route-coverage-gate` is required metadata-only evidence for
AIHub endpoint wiring. It inventories text, streaming text, PDF, image, video,
audio, and transcription endpoints for runtime-router coverage, budget-decision
coverage, route telemetry coverage, usage recording, response route payloads,
and media/speech catalog review gaps. It does not call providers, gateways,
app AI endpoints, models, or the network, and it does not claim that
media/speech defaults are price-benchmarked.

`aihub-media-speech-default-catalog-gate` is required metadata-only evidence for
AIHub media and speech default review. It is exposed at
`/api/v1/aihub/models/aihub-media-speech-default-catalog-gate` and reviews
image, video, audio, transcription, future Live audio, and embedding default
coverage against endpoint route coverage, local catalog status, explicit
media/speech budget modes, official Gemini/Veo/TTS source anchors, default
release actions, and review items. Non-catalog and future-route defaults remain
explicit-review only. The gate does not call providers, gateways, app AI
endpoints, models, or the network, write configuration, change defaults, shift
traffic, or return request/response bodies, headers, prompts, raw payloads,
audio, transcripts, legal text, model output, gateway responses, credentials,
emails, or user identifiers.

`aihub-media-runtime-compatibility-gate` is required metadata-only evidence for
AIHub media runtime endpoint shapes. It is exposed at
`/api/v1/aihub/models/aihub-media-runtime-compatibility-gate` and separates the
current OpenAI-compatible `client.videos.create`/`retrieve`,
`client.audio.speech.create`, and `client.audio.transcriptions.create` code
paths from native Gemini/Veo/TTS/Live runtime requirements. Veo, Gemini TTS,
Gemini audio-understanding, and Live audio promotion remain review-only until
gateway shape, native adapter, polling, session, and output-extraction evidence
is attached. The gate does not call providers, gateways, app AI endpoints,
models, or the network, write configuration, change defaults, shift traffic, or
return request/response bodies, headers, prompts, raw payloads, audio,
transcripts, legal text, model output, gateway responses, credentials, emails,
or user identifiers.

`gemini-embedding-cheap-first-preflight` is required metadata-only evidence for
embedding default review. It is exposed at
`/api/v1/aihub/models/gemini-embedding-cheap-first-preflight` and records
`APP_AI_EMBEDDING_MODEL=gemini-embedding-001`, `auto-embedding` alias coverage,
local catalog pricing, cheap-first embedding budget policy, and multimodal
`gemini-embedding-2` review routing. Multimodal `gemini-embedding-2` remains
review-required before image, audio, video, PDF, or source-index use. The
preflight does not call providers, gateways, app AI endpoints, models, or the
network, write configuration, change defaults, write indexes, shift traffic, or
return source text, raw legal text, source chunks, embedding vectors,
request/response bodies, headers, prompts, raw payloads, model output, gateway
responses, credentials, emails, or user identifiers.

`gentxt-routing-guard` is required metadata-only evidence for the text endpoint
task boundary. It verifies that media and speech routing aliases are rejected
for `POST /api/v1/aihub/gentxt` and remain scoped to media endpoints. It does
not call providers, gateways, app AI endpoints, models, or the network, write
configuration, shift traffic, or return prompts, request bodies, response
bodies, raw payloads, legal text, model output, gateway responses, credentials,
emails, or user identifiers.

`catalog-source-audit` is required evidence for source-backed Gemini catalog maintenance. It checks official source URL coverage, pricing metadata visibility, stable Flash-Lite high-frequency defaults, and preview/premium default drift before model changes are promoted.

`gemini-official-model-family-roadmap-evidence` is required evidence for
official Gemini family coverage. It keeps Gemini 2.5 stable Flash-Lite
cheap-first defaults, Gemini 3 and image review/explicit-route boundaries, and
Live/audio, embedding, and TTS gap queues visible before maintainers claim
support for additional Gemini families.

`route-telemetry-repository` and downstream route telemetry summaries estimate
`estimated_cost_usd` for known Gemini/NewAPI catalog model routes from local
catalog token pricing. Unknown gateway model ids remain at `0` estimated cost
and continue through unknown model review. Known catalog models without token
pricing metadata are counted in `unpriced_model_count`, which keeps catalog
pricing gaps separate from unknown gateway model traffic.

`cheap_first_release_decision` is a downstream release decision packet that uses
readiness plus cheap-first calibration, Gemini variant review, catalog source
audit, route preflight, route quality, failure upgrade budget, escalation budget, price refresh, and ModelOps performance
signals to decide whether current cheap-first defaults can remain and whether
new default promotion requires maintainer review.

The readiness warning drilldown is release evidence for maintainers reviewing cheap-first model changes. It makes warning ownership visible without exposing legal text, prompts, model output, provider credentials, request bodies, response bodies, or gateway payloads.

## Official Price And Status Gate

ModelOps readiness must treat any model with unconfirmed official provider or
gateway pricing, lifecycle status, or availability as `unpriced` and
`review-only`. Such a model cannot satisfy cheap-first cost evidence, cannot be
counted in savings claims, and cannot be promoted into defaults until
source-backed price, status, capability, and gateway evidence are refreshed.

## Release Readiness

`model-ops-readiness` is a required release-readiness check. Maintainers should run:

```bash
python -m pytest tests/test_model_failure_upgrade_budget.py tests/test_model_ops_cheap_first_escalation_budget.py tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression
```

## Safety

The service only aggregates existing status and summary metadata. It does not store prompts, documents, file names, API keys, passwords, emails, user identifiers, raw payloads, gateway responses, or raw model output.

## Related files

- `app/backend/services/model_ops_readiness.py`
- `app/backend/services/model_ops_cheap_first_release_decision.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/maintenance_evidence.py`
- `app/backend/services/model_default_optimization.py`
- `app/backend/services/model_gateway_compatibility.py`
- `app/backend/services/model_gateway_health_plan.py`
- `app/backend/services/model_gateway_probe_evaluation.py`
- `app/backend/services/model_lifecycle_policy.py`
- `app/backend/services/model_catalog_source_audit.py`
- `app/backend/services/model_ops_gemini_official_model_family_roadmap.py`
- `app/backend/services/model_request_cost_bounds.py`
- `app/backend/services/model_cache_policy.py`
- `app/backend/services/route_telemetry_repository.py`
- `app/backend/services/route_telemetry_ops_summary.py`
- `app/backend/services/route_telemetry_triage_queue.py`
- `app/backend/services/route_telemetry_remediation_plan.py`
- `app/backend/services/gemini_newapi_cheap_first_calibration.py`
- `app/backend/services/model_ops_performance_budget.py`
- `app/backend/services/model_route_quality_budget.py`
- `app/backend/services/model_failure_upgrade_budget.py`
- `app/backend/services/model_ops_gemini_cheap_first_route_preflight.py`
- `app/backend/services/modelops_observed_gateway_model_fit_matrix.py`
- `app/backend/services/model_ops_runtime_explicit_model_fit_gate.py`
- `app/backend/services/model_ops_aihub_endpoint_route_coverage_gate.py`
- `app/backend/services/model_ops_aihub_media_speech_default_catalog_gate.py`
- `app/backend/services/model_ops_aihub_media_runtime_compatibility_gate.py`
- `app/backend/services/modelops_legal_micro_benchmark_preflight.py`
- `app/backend/services/model_ops_cheap_first_escalation_budget.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_model_ops_readiness.py`
- `app/backend/tests/test_release_readiness.py`
- `app/backend/tests/test_continuous_update_ledger.py`
- `app/backend/tests/test_maintenance_evidence.py`
- `app/backend/tests/test_model_ops_cheap_first_release_decision.py`
- `app/backend/tests/test_model_ops_performance_budget.py`
- `app/backend/tests/test_model_route_quality_budget.py`
- `app/backend/tests/test_model_failure_upgrade_budget.py`
- `app/backend/tests/test_model_ops_gemini_cheap_first_route_preflight.py`
- `app/backend/tests/test_modelops_observed_gateway_model_fit_matrix.py`
- `app/backend/tests/test_model_ops_runtime_explicit_model_fit_gate.py`
- `app/backend/tests/test_model_ops_aihub_endpoint_route_coverage_gate.py`
- `app/backend/tests/test_model_ops_aihub_media_runtime_compatibility_gate.py`
- `app/backend/tests/test_modelops_legal_micro_benchmark_preflight.py`
- `app/backend/tests/test_model_ops_cheap_first_escalation_budget.py`
- `app/backend/tests/test_model_default_optimization.py`
- `app/backend/tests/test_model_gateway_compatibility.py`
- `app/backend/tests/test_model_gateway_health_plan.py`
- `app/backend/tests/test_model_gateway_probe_evaluation.py`
- `app/backend/tests/test_model_lifecycle_policy.py`
- `app/backend/tests/test_model_catalog_source_audit.py`
- `app/backend/tests/test_model_ops_gemini_official_model_family_roadmap.py`
- `app/backend/tests/test_model_request_cost_bounds.py`
- `app/backend/tests/test_model_cache_policy.py`
- `app/backend/tests/test_route_telemetry_repository.py`
- `app/backend/tests/test_route_telemetry_ops_summary.py`
- `app/backend/tests/test_route_telemetry_triage_queue.py`
- `app/backend/tests/test_route_telemetry_remediation_plan.py`
- `app/backend/tests/test_gemini_newapi_cheap_first_calibration.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
- `docs/MODEL_FAILURE_UPGRADE_BUDGET.md`
- `docs/MODELOPS_GEMINI_OFFICIAL_MODEL_FAMILY_ROADMAP.md`
- `docs/MODELOPS_GEMINI_CHEAP_FIRST_ROUTE_PREFLIGHT.md`
- `docs/MODELOPS_LEGAL_MICRO_BENCHMARK_PREFLIGHT.md`
