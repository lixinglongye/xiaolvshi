# Continuous Update Ledger

Latest product-quality slice: `legal-document-benchmark-coverage`, `legal-document-benchmark-coverage-ui`, and `legal-document-coverage-claim-policy` add a metadata-only legal document coverage matrix, maintenance route, tests, UI panel, and claim-review gate for low-resource fixture planning. The claim policy keeps broad, real-client, public-benchmark, and unsupported document coverage wording blocked.

Follow-up slice: `legal-document-benchmark-gap-fixtures` adds synthetic evidence-catalog, settlement-agreement, legal-opinion, and defense-answer fixtures so the current local coverage matrix reaches 7/7 target document types. This still does not prove broad real-world document coverage or live model accuracy.

Current claim-policy slice: `legal-document-coverage-claim-policy` allows only repository-backed synthetic fixture wording and keeps LegalBench, LexGLUE, LegalBench-RAG, LexEval, CaseGen, COLIEE, CUAD, leaderboard, real-client, and universal legal-document claims out of release evidence unless separate public proof exists.

Current research refresh slice: `legal-benchmark-research-refresh` adds
metadata-only maintenance evidence for refreshing LegalBench, LexGLUE,
LegalBench-RAG, LexEval, CaseGen, COLIEE, and adoption-bridge mappings. It records expected backend service/test evidence
paths and release links only; it does not download datasets, claim public
benchmark scores, store external legal text, call models, or handle
credentials.

Current routing-risk slice: `model-route-legal-benchmark-risk-queue` adds a
metadata-only maintainer queue that joins cheap-first Gemini/NewAPI calibration,
legal benchmark refresh mappings, and user-need coverage. It does not call
gateways, write model routes, download datasets, claim public benchmark scores,
store raw legal text, or handle credentials.

Current user-need priority slice: `user-need-implementation-priority-queue`
adds metadata-only evidence that joins high-priority user needs, legal benchmark
coverage gaps, cheap-first calibration/model routing risk, and product
execution actions into a reviewable implementation queue. It does not download
public datasets, call NewAPI, Gemini, OpenAI, Google, gateways, or the network,
write real env values, or include raw legal text, prompts, payloads, model
outputs, or credentials.

Current user-need Gemini route slice: `user-need-gemini-route-coverage` adds
metadata-only route coverage evidence that joins user-need benchmark coverage,
cheap-first calibration tasks, and Gemini route preflight rows. It shows
Flash-Lite protected needs, premium/benchmark/license review gaps, and unmapped
route blockers without public dataset downloads, benchmark sample imports,
NewAPI/Gemini/OpenAI/Google/gateway/app-AI/network calls, configuration writes,
default route changes, traffic shifts, raw legal text, prompts, route payloads,
model outputs, credentials, emails, or user identifiers.

Current Legal RAG authority slice: `legal-rag-authority-citation-gate` adds a
metadata-only authority and citation gate for selected-source ids, authority
tiers, jurisdiction/date/freshness metadata, and citation-map source ids. It
does not call NewAPI, Gemini, or gateways, download datasets, store raw legal
text, prompts, model outputs, or credentials.

Current Legal RAG hallucination slice: `legal-rag-hallucination-triage-gate`
adds a metadata-only triage gate for local failure fixture labels, severity,
reviewer actions, release blockers, and authority-gate rows. It does not call
NewAPI, Gemini, or gateways, download datasets, store raw legal text, retrieved
snippets, prompts, model outputs, or credentials.

Current model-ops slice: `model-price-refresh-monitor-readiness-ui` wires the
Gemini/NewAPI price refresh monitor into `/api/v1/aihub/models`, model-ops
readiness, and the `/model-ops` reviewer page. Unknown, preview, premium, or
unpriced gateway models now surface as release-review evidence before they can
be treated as cheap-first defaults.

Current catalog-derived default evidence: `model-default-candidate-selector`
adds a metadata-only Gemini/NewAPI selector that derives cheapest capable task
recommendations and ladders from local catalog capability, lifecycle, price,
cost-tier, and latency metadata. Runtime defaults remain unchanged; the selector
only gives ModelOps a reviewable signal when a future stable lower-cost
Flash-Lite catalog row is `default_eligible` and should replace a hard-coded
recommendation. The ladder must keep `default_eligible` rows separate from
`review-only` rows; preview, unpriced, premium-over-budget,
premium-exception-only, unknown, deprecated, and media-route rows are review
context only and must not be treated by UI or maintainers as directly
promotable defaults. It does not write env files, call gateways, shift traffic,
include raw prompts, legal text, model outputs, or credentials.

Newest model-ops release evidence: `modelops-cheap-first-canary-rollback-drill`
adds a shipped metadata-only rollback rehearsal packet downstream of canary
approval evidence. It records trigger review, holdout confirmation, role, and
checklist labels only; it does not execute rollback, write configuration,
persist drill state, call gateways, or shift production traffic.

Follow-up model-ops release evidence:
`modelops-cheap-first-canary-change-manifest` adds a shipped metadata-only
manifest for proposed cheap-first default edits. It records external change-set
metadata, prerequisites, rollback-drill status, validation commands, and
operator steps only; it does not write configuration, write env files, store
secret values, call gateways, record approver identity, apply changes, or shift
traffic.

Current agentic/grounded defaults evidence: `modelops-agentic-grounded-defaults`
adds shipped metadata-only/default routing evidence for `APP_AI_AGENTIC_MODEL`
(`gemini-3.1-flash-lite`) and `APP_AI_GROUNDED_RESEARCH_MODEL`
(`gemini-3.1-flash-lite`) so ModelOps can review the agentic and grounded-research
defaults without NewAPI/Gemini/OpenAI/Google/gateway/network calls, real
environment writes, raw prompts, payloads, model outputs, or credentials.

Current env/template alignment evidence: `modelops-default-template-alignment`
adds shipped metadata-only audit evidence that keeps Settings defaults,
`app/backend/.env.example`, the README env block, and `docs/AI_MODEL_STRATEGY`
aligned for Gemini cheap-first defaults, including `APP_AI_AGENTIC_MODEL` and
`APP_AI_GROUNDED_RESEARCH_MODEL` pinned to `gemini-3.1-flash-lite`. It does not
call NewAPI, Gemini, OpenAI, Google, gateways, or the network, write real
environment values, or include raw prompts, payloads, model outputs, or
credentials.

Current Gemini default proposal evidence:
`modelops-gemini-default-change-review` adds shipped metadata-only proposal
review evidence for maintainers before changing a task default model to a new
Gemini variant. It records the review scope for cost tier, lifecycle,
capabilities, gateway compatibility, and the premium/manual review boundary
only; it does not call NewAPI, Gemini, OpenAI, Google, gateways, or the network,
write real environment values, or include raw prompts, payloads, model outputs,
or credentials.

Current Gemini default cost evidence:
`modelops-gemini-default-cost-impact` adds shipped metadata-only cost impact
forecast evidence for maintainers before changing a task default model to a new
Gemini variant. It records the review scope for estimated monthly cost delta,
cheap-first savings or regression, unknown pricing, and the premium
exception/manual review boundary only; it does not call NewAPI, Gemini, OpenAI,
Google, gateways, or the network, write real environment values, or include raw
prompts, payloads, model outputs, or credentials.

Current observed Gemini model intake evidence:
`modelops-observed-gemini-model-intake-queue` adds shipped metadata-only intake
queue evidence for OpenAI-compatible gateway `/models` or manually observed
Gemini-like model ids before they enter default candidates. It records
normalization scope, known/unknown status, price, lifecycle, cost tier,
cheap-first eligibility, and default-promotion block/review/ready state only;
it does not call NewAPI, Gemini, OpenAI, Google, gateways, or the network,
write real environment values, or include raw prompts, payloads, model outputs,
or credentials.

Current observed Gemini coverage gap evidence:
`modelops-observed-gemini-coverage-gap-queue` adds shipped metadata-only
coverage queue evidence for sanitized observed Gemini-like model ids. It joins
the observed intake queue with the Gemini variant matrix, then records family
coverage gaps, high-frequency cheap-first task gaps, unknown/unpriced/preview/
media risk, and default-promotion review actions only. It does not call NewAPI,
Gemini, OpenAI, Google, gateways, or the network, write configuration, shift
traffic, or include raw prompts, payloads, model outputs, credentials, or
emails.

Current model catalog candidate patch evidence:
`model-catalog-candidate-patch-plan` adds shipped metadata-only catalog
maintenance evidence for unknown observed Gemini-like model ids. It records
manual `ModelProfile` candidate stubs, required source/pricing/lifecycle/
capability/gateway-probe checks, cheap-first boundaries, and explicit-only
default-promotion states. It does not edit `model_catalog.py`, write
configuration, call NewAPI, Gemini, OpenAI, Google, gateways, or the network,
shift traffic, or include raw payloads, prompts, legal text, model outputs,
credentials, or emails.

Current gateway request compatibility evidence:
`model-gateway-request-compatibility-gate` adds shipped metadata-only
OpenAI-compatible Gemini/NewAPI request-shape evidence for task defaults,
gateway model compatibility, request parameter caps, reasoning-effort policy,
JSON response-format requirements, and cheap-first cost bounds. It does not
call NewAPI, Gemini, OpenAI, Google, gateways, or the network, write
configuration, shift traffic, or include headers, request bodies, prompts, raw
legal text, model outputs, payloads, emails, or credentials.

Current gateway connection profile evidence:
`model-gateway-connection-profile` adds shipped metadata-only OpenAI-compatible
gateway connection evidence. It normalizes remote bare hosts such as
`https://yibuapi.com` to `/v1` for runtime client setup, flags credential-bearing
URLs and insecure remote HTTP, and reports key presence only through
`{{APP_AI_KEY}}`. It does not call NewAPI, Gemini, OpenAI, Google, gateways, app
AI endpoints, or the network, write configuration, shift traffic, or include API
keys, Authorization headers, request bodies, response bodies, prompts, raw
payloads, legal text, model outputs, gateway responses, emails, or user
identifiers.

Current Gemini cheap-first route preflight evidence:
`modelops-gemini-cheap-first-route-preflight` adds shipped metadata-only route
preflight evidence for official source refresh notes, local Gemini task
defaults, variant review states, alias capability coverage, and cheap-first
coverage-gate status. It keeps high-frequency work on stable Flash-Lite routes
while preview, premium, media, unknown, unpriced, or retired variants remain
review/explicit-only. It does not call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, or the network, write configuration, shift traffic,
claim live model quality, or include request/response bodies, headers, prompts,
raw payloads, legal text, model outputs, gateway responses, credentials, emails,
or user identifiers.

Current observed gateway model fit evidence:
`modelops-observed-gateway-model-fit-matrix` adds shipped metadata-only
NewAPI/Gemini/OpenAI-compatible observed gateway model fit evidence. It maps
sanitized `/models` inventory IDs to canonical catalog rows, cheapest observed
task candidates, cheap-first coverage, missing task gaps, and review-only Pro,
preview, media, unknown, external, or unpriced boundaries. It does not call
NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the
network, validate live account inventory, write configuration, shift traffic, or
include API keys, Authorization headers, request bodies, response bodies,
prompts, raw payloads, legal text, model outputs, gateway responses, emails, or
user identifiers.

Current AIHub endpoint route coverage evidence:
`modelops-aihub-endpoint-route-coverage-gate` adds shipped metadata-only
endpoint route coverage evidence for text, streaming text, PDF, image, video,
audio, and transcription AIHub routes. It shows runtime-router coverage,
budget-decision coverage, route telemetry coverage, response route-payload
coverage, and legacy media route gaps without calling NewAPI, Gemini, OpenAI,
Google, gateways, app AI endpoints, models, or the network, writing
configuration, shifting traffic, or including request/response bodies, headers,
prompts, raw payloads, legal text, model outputs, gateway responses,
credentials, emails, or user identifiers.

Current legal micro benchmark preflight evidence:
`modelops-legal-micro-benchmark-preflight` adds shipped metadata-only
low-resource legal benchmark run-planning evidence for cheap-first Gemini
fixture ids, document case ids, fact-consistency case ids, serial run order,
cost estimates, and follow-up gate bindings. It does not call NewAPI, Gemini,
OpenAI, Google, gateways, app AI endpoints, or the network, write
configuration, shift traffic, claim live model quality, or include request
bodies, messages, prompts, fixture excerpts, legal text, generated document
text, model outputs, gateway responses, credentials, or emails.

Current route telemetry UI regression evidence:
`route-telemetry-ui-regression-contract` hardens the `/model-ops` source
contract for route telemetry repository, operations summary, triage queue, and
remediation panels. It keeps cheap-first routing warnings, sanitized route
counters, no-config-write boundaries, and no-NewAPI-call boundaries visible
without rendering prompts, legal text, request bodies, response bodies, headers,
raw model output, emails, or credentials.

Current route telemetry cost evidence:
`route-telemetry-catalog-cost-estimation` calculates persisted
`estimated_cost_usd` from local Gemini catalog token prices for known
NewAPI/Gemini routes. Unknown gateway models stay unpriced and continue to
surface through unknown-model counters, so cheap-first cost review remains
metadata-only and does not store prompts, legal text, model outputs, payloads,
emails, or credentials.

Current runtime route reason-code evidence:
`runtime-route-reason-codes` adds bounded route policy labels for cheap-first
downgrades, unknown catalog models, over-budget requests, operator-review
gates, and explicit reviewed overrides. The repository persists only sanitized
reason-code lists and aggregate counts, and the ModelOps table shows those
counts without storing prompts, legal text, model outputs, payloads, emails, or
credentials.

Current route telemetry reason-code hotspot evidence:
`route-telemetry-reason-code-hotspots` turns sanitized aggregate
`reason_code_counts` into ops summary top reason codes, daily hotspot rows, and
triage actions for `over_task_budget`, `operator_review_required`,
`unknown_catalog_model`, `gateway_passthrough`, and `unknown_reason_code`.
The evidence remains metadata-only and does not call NewAPI/Gemini/gateways,
write configuration, or store prompts, legal text, model outputs, payloads,
emails, or credentials.

Current ModelOps performance release evidence:
`modelops-performance-observation-release-binding` binds sanitized
`POST /api/v1/aihub/models/performance-budget` observations back into aggregate
ModelOps readiness and the cheap-first release decision. Slow timing rows now
require maintainer review or block default promotion in the POST response and
later in-process `/api/v1/aihub/models` aggregate payloads without storing raw
payloads, URLs, headers, emails, credentials, prompts, legal text, gateway
responses, model output, or making network calls.

Current legal document benchmark alignment evidence:
`legal-document-template-benchmark-alignment` aligns the legal-document
template matrix with local benchmark coverage targets through canonical
`benchmark_document_type` IDs. It adds defense-answer fixture coverage,
legal-opinion template delivery rules, and a UTF-8 readability guard for mock
templates without model calls, dataset downloads, raw client documents, prompts,
model outputs, emails, or credentials.

Current Legal RAG citation blocker evidence:
`legal-rag-missing-answer-citation-blocker` blocks local Legal RAG evaluation
artifacts when expected or retrieved legal source IDs exist but the generated
answer provides no citation source IDs. It forces citation precision to zero and
returns metadata-only coverage flags without raw retrieval context, answer text,
prompts, model output, credentials, or network calls.

Current legal fixture cheap-first benchmark gate evidence:
`modelops-legal-fixture-cheap-first-benchmark-gate` adds shipped metadata-only
small legal-document cheap-first Gemini benchmark/risk gate evidence. It records
only redacted fixture ids, document case ids, expected issue counts, document
benchmark pass/fail counts, coverage-gap counts, cost metadata, and escalation
metadata for reviewer routing; it does not call NewAPI, Gemini, OpenAI, Google,
gateways, or the network, and it does not include real legal text, fixture
snippets, candidate generated text, prompts, model outputs, credentials, or
emails.

Current legal fixture cheap-first default promotion packet evidence:
`modelops-legal-fixture-cheap-first-default-promotion-packet` adds shipped
metadata-only maintainer review evidence for cheap-first legal fixture default
promotion. It records fixture ids, document case ids, gate status, document
benchmark pass/fail counts, coverage-gap counts, cost-tier metadata, reason
codes, and required signoff roles only. It does not write configuration, call
NewAPI, Gemini, OpenAI, Google, gateways, or the network, shift traffic, or
include real legal text, fixture snippets, generated document text, prompts,
model outputs, credentials, or emails.

This ledger records progress toward the long-running maintenance target without claiming completion before it is reviewable.

## Endpoint

```http
GET /api/v1/maintenance/continuous-update-ledger
POST /api/v1/maintenance/continuous-update-ledger
```

The response includes:

- `status`: currently `in_progress`.
- `goal`: the 24-hour and 100+ medium/large update targets.
- `summary`: completed count, remaining count, category counts, and completion flags.
- `completed_updates`: shipped updates with code, test, doc, or UI evidence paths.
- `next_update_queue`: planned medium/large work, prioritized for cheap-first and low-resource validation.
- `low_resource_fixture_evidence`: archive-safe local fixture evidence status.
- `low_resource_test_policy`: fixture limits, serial execution policy, default benchmark endpoint, ledger review endpoint, and run-monitor review endpoint.
- `validation_commands`: small pytest commands that can run on a local laptop.

Current case workbench runtime evidence:
`case-workbench-risk-refresh-plan` adds shipped metadata-only risk/evidence
refresh planning to repository-backed workbench payloads. It reads sanitized
section counts and event deltas, lists section/event ids that need follow-up,
and keeps live risk-state writes, evidence graph refreshes, notifications, raw
event payloads, legal text, and client contact details outside the ledger claim.

`POST` accepts the same compact low-resource fixture payload used by
`/legal-review-benchmark/local-run-review`, either directly or under
`low_resource_fixture_review`. The ledger internally builds the local run review
and result archive, then returns only:

- review/archive status labels,
- release decision labels,
- observed, archived, not-run, redacted, dropped-raw-field, blocking, warning,
  request, and cost counts,
- safe check ids,
- source endpoint labels, and
- an explicit privacy boundary.

It does not return `run_report_payload`, raw gateway responses, `choices`,
`output_text`, prompts, headers, credentials, emails, legal text, or model
outputs. Submitted fixture evidence does not mutate
`completed_medium_large_update_count` and does not change `completion_ready`.
The same `low_resource_fixture_review` wrapper can also be POSTed to
`/api/v1/maintenance/continuous-session-run-monitor` so the active-run monitor
can show the archive-safe fixture evidence status without claiming 24-hour
completion.

Recent integrated batches moved case workbench persistence planning, legal
source durable index planning, billing quota migration planning, validated
repository implementations, service-level runtime/RAG/entitlement bindings,
authenticated runtime/RAG/billing usage routes, and typed frontend API clients
from the queue into shipped evidence. The latest frontend batch also ships the
main-app runtime router discovery smoke, a case overview runtime state/event
panel, a metadata-only legal RAG research panel, and a global billing quota
badge. The current follow-up evidence adds a read-only billing report preflight
route, privacy-safe case edit runtime events for material/evidence/fact/task
changes, metadata-only Legal RAG context cache/copy controls, a best-effort
document-generation quota consumption attempt, server-side generated_documents
CRUD quota guards, case evidence-catalog/civil-complaint quota guards,
deep-review first-principles document-generation quota guards,
selected-source Legal RAG request metadata propagation, metadata-level
selected-source citation validation, a metadata-only maintenance self-check
route for selected-source validation, a local-only billing payment
reconciliation policy, task runtime notification summaries, a deterministic
laptop-safe legal document benchmark suite, a LegalBench/LexGLUE/LegalBench-RAG/LexEval/CaseGen/COLIEE
research registry mapped to low-resource local tests, a metadata-only research
refresh slice for that registry, and a maintenance UI section for that
registry. The latest adoption-research bridge joins public
legal-AI research, professional AI governance/adoption signals, existing user
needs, product feature gaps, cheap-first validation commands, and release gates
without storing survey free text, raw benchmark samples, legal text, model
outputs, or secrets.
The current Legal RAG authority/citation gate joins source authority metadata,
selected-source validation, freshness policy, and frontend regression evidence
without storing legal snippets, prompts, generated analysis, gateway payloads,
or credentials.
The latest model-ops batch adds a route telemetry operations summary that turns
sanitized persisted route aggregates into release-review checks for failures,
premium-model drift, over-budget pressure, operator-review load, unknown
models, and cheap-first downgrade evidence.
The follow-up triage queue converts those checks into prioritized maintainer
actions, including daily hotspots and missing staging telemetry, without
copying raw route events or model payloads.
The newest remediation plan maps those triage actions to operator-reviewed
cheap-first repair steps, env suggestions, and validation commands without
writing config or calling NewAPI/Gemini.
This batch also adds deep-review selected-source report binding, quota delivery
decisions for export/client delivery/account-plan review, deterministic feedback
issue clustering, metadata-only evidence bundle integrity checks, privacy
retention rules, release-claim compliance checks, case export readiness checks,
a real deep-review export readiness route gate, OCR readiness runtime binding
for uploaded deep-review polling, and admin audit policy evidence. The
medium/large update count is now at or above 100, but the goal is still not
complete because the 24-hour continuous validation window remains unproven.
These are reviewable product slices; they do not finish real payment provider
settlement or webhook verification, automatic deep-review report binding for
selected-source validation, raw contract extraction, or a database-backed team
workspace.

## Completion Policy

The ledger must not mark the goal complete until both conditions are true:

1. A full 24-hour window is backed by timestamped commits, test runs, or validation records.
2. At least 100 medium/large updates are reviewable in the repository.

The second condition is currently satisfied by repository evidence. The first
condition is still unsatisfied, so `completion_ready` remains `false`.

Small legal fixture tests can count only when they produce repository-backed evidence such as a service, test, documentation update, endpoint, or reviewer-facing UI change. Local-only experiments, raw model outputs, account credentials, and client documents must not be committed.

`docs/CONTINUOUS_SESSION_EVIDENCE.md` defines the reviewer-facing contract for
the 24-hour session validator, and
`POST /api/v1/maintenance/continuous-session-evidence` evaluates explicit
session metadata. The ledger should continue to expose the 100+ update count
separately from the continuous-time proof so a reviewer can see that update
volume is satisfied while the time-window gate remains open. The validator
joins timestamped commits, tests, pushes, review actions, credential scans, and
low-resource legal fixture records without copying raw legal text or model
output into repository evidence.

`docs/CONTINUOUS_SESSION_TIMELINE.md` defines the implemented reviewer timeline
for `GET`/`POST` `/api/v1/maintenance/continuous-session-timeline`. That
endpoint consumes metadata only and merges the ledger, session validator,
heartbeat, low-resource legal fixture, and release review evidence streams. It
must not store secrets, account data, emails, raw legal text, raw gateway
payloads, or model original outputs, and it must keep `completion_ready` blocked
until the 24-hour window is actually proven.

`docs/GIT_HISTORY_EVIDENCE.md` defines the implemented reviewer contract for
`GET /api/v1/maintenance/git-history-evidence`. That endpoint computes real
commit cadence from Git commit metadata, including commit count, longest
cadence window, and maximum adjacent-commit gap. The ledger cites those metrics
as cadence evidence only. It must not treat commit metadata as automatic proof
that tests ran, commits were pushed, credential scans passed, or low-resource
legal fixtures executed.

`docs/VALIDATION_EVENT_EVIDENCE.md` defines the upcoming metadata-only contract
for `GET`/`POST` `/api/v1/maintenance/validation-event-evidence`. That endpoint
can add non-git validation rows for input validation tests, `credential_scan`,
`push`, `review`/`release_review`, and `legal_fixture` events. Accepted records
should contain only timestamps, opaque check/run/validation IDs, optional
commit hashes, statuses, labels, and repository evidence paths. They must not
store raw stdout, raw stderr, logs, complete legal text, raw model output,
credentials, emails, or passwords, and they do not make the 24-hour target
complete by themselves.

`docs/CONTINUOUS_SESSION_REVIEW_PACKET.md` defines the upcoming
`GET`/`POST` `/api/v1/maintenance/continuous-session-review-packet` endpoint.
That endpoint packages the ledger, continuous-session timeline, git-history
cadence, and validation-event evidence into a metadata-only reviewer/support
packet. The packet may expose section statuses, hashes, repository
`evidence_paths`, blockers, review questions, and the privacy boundary, but not
raw logs, stdout, stderr, complete legal text, raw model output, credentials,
or emails. It is an evidence index only and must not claim the 24-hour target is
ready unless real timestamped events and the 100+ update evidence both pass the
joined gate.

`docs/CONTINUOUS_SESSION_RUN_MONITOR.md` defines the implemented
`GET`/`POST` `/api/v1/maintenance/continuous-session-run-monitor` endpoint.
That endpoint monitors an active maintenance run by joining ledger, timeline,
and review-packet metadata into elapsed-hour, current-gap, checkpoint,
required-evidence, blocker, and next-action fields. It is metadata-only and
does not prove 24h completion by itself. The ledger must treat it as an
operational monitor until real timestamped events pass the joined evidence
gate. It must not store raw logs, legal text, model outputs, credentials, or
emails.

`docs/GEMINI_NEWAPI_MODEL_SELECTOR.md` defines the metadata-only
`GET`/`POST` `/api/v1/maintenance/gemini-newapi-model-selector` endpoint. It
indexes Gemini/NewAPI model id normalization, task labels, cost tiers, candidate
chains, warnings, and evidence paths for cheap-first selection review. It must
not store API keys, gateway credentials, prompts, raw legal text, raw model
outputs, or emails, and it must not be counted as proof that NewAPI was called
or that the 24-hour continuous window is complete.

`docs/GEMINI_NEWAPI_MODEL_ALIAS_MATRIX.md` defines the metadata-only
`GET`/`POST` `/api/v1/maintenance/gemini-newapi-model-alias-matrix` endpoint.
It maps canonical, `models/`, `google/`, `google:`, `yibu/`, and nested
provider Gemini aliases to catalog ids, cheap-first eligibility, premium/manual
review boundaries, and unknown-model review states. It stores sanitized alias
metadata only, rejects sensitive or malformed observed values into separate
sensitive/invalid/total rejection counts, and does
not prove live NewAPI execution or 24-hour completion.

`docs/GEMINI_NEWAPI_SELECTOR_REPLAY.md` defines the metadata-only
`GET`/`POST` `/api/v1/maintenance/gemini-newapi-selector-replay` endpoint. It
replays deterministic selector scenarios for fast/classification/OCR
cheap-first behavior, review/document_generation balanced-after-precheck,
large_pdf/final_review premium exceptions, unknown Gemini-like catalog review,
and high-frequency explicit premium blocking or warning. Submitted rationale is
not echoed. It stores selector regression metadata only and cannot prove live
NewAPI execution or 24-hour completion.

## Low-Resource Test Path

For small machines, use the existing quick suite first:

```http
GET /api/v1/maintenance/legal-review-benchmark/quick-suite?fixture_limit=2
```

The runtime route discovery smoke can run from `app/backend`:

```powershell
python -m pytest tests/test_runtime_router_discovery.py -q
```

This keeps:

- `max_parallel_requests` at `1`.
- Network access disabled by default.
- Public benchmark sources as metadata only until license and attribution review pass.
- Model calls manual and serial.

For 24-hour evidence, each small legal-document run should add only a compact
metadata record: fixture IDs, route labels, coverage score, command label,
timestamp, and repository evidence paths. This lets the same low-resource tests
support both product quality checks and the continuous maintenance timeline.
Commit metadata can sit beside those records to show cadence, but it cannot
replace the fixture record itself.

If a maintainer needs to attach one local fixture result to the ledger, use the
same pasted payload from the maintenance page local-run-review flow. The ledger
will show `Ledger fixture evidence` with observed/archived counts and raw-field
drop counts while keeping update totals and 24-hour readiness unchanged.

## Related Files

- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/continuous_session_evidence.py`
- `app/backend/services/continuous_session_run_monitor.py`
- `app/backend/tests/test_continuous_update_ledger.py`
- `app/backend/tests/test_continuous_session_evidence.py`
- `docs/GIT_HISTORY_EVIDENCE.md`
- `docs/VALIDATION_EVENT_EVIDENCE.md`
- `docs/CONTINUOUS_SESSION_REVIEW_PACKET.md`
- `docs/CONTINUOUS_SESSION_RUN_MONITOR.md`
- `docs/GEMINI_NEWAPI_MODEL_SELECTOR.md`
- `docs/GEMINI_NEWAPI_SELECTOR_REPLAY.md`
- `docs/MODEL_OPS_CHEAP_FIRST_CANARY_ROLLBACK_DRILL.md`
- `docs/MODEL_OPS_CHEAP_FIRST_CANARY_CHANGE_MANIFEST.md`
- `docs/MODELOPS_GEMINI_CHEAP_FIRST_ROUTE_PREFLIGHT.md`
- `docs/USER_NEED_GEMINI_ROUTE_COVERAGE.md`
- `docs/LEGAL_BENCHMARK_RESEARCH_REFRESH.md`
- `docs/MODEL_ROUTE_LEGAL_BENCHMARK_RISK_QUEUE.md`
- `docs/LEGAL_ADOPTION_RESEARCH_BRIDGE.md`
- `docs/DEEP_REVIEW_EXPORT_READINESS_GATE.md`
- `docs/CONTINUOUS_SESSION_EVIDENCE.md`
- `docs/CONTINUOUS_SESSION_TIMELINE.md`
- `app/backend/main.py`
- `app/backend/routers/maintenance.py`
- `app/backend/alembic/versions/b7a2c9d4e6f1_repository_persistence_indexes.py`
- `app/backend/models/billing_quota_idempotency_keys.py`
- `app/backend/models/billing_quota_usage_counters.py`
- `app/backend/models/case_workbench_section_states.py`
- `app/backend/models/case_workbench_state_events.py`
- `app/backend/models/legal_source_index_entries.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/billing_entitlement_gap.py`
- `app/backend/routers/billing_usage.py`
- `app/backend/services/billing_quota_migration_plan.py`
- `app/backend/services/billing_quota_persistence_plan.py`
- `app/backend/services/billing_quota_repository.py`
- `app/backend/services/billing_entitlement_quota_binding.py`
- `app/backend/services/billing_usage_quota_policy.py`
- `app/backend/services/billing_payment_reconciliation.py`
- `app/backend/routers/generated_documents.py`
- `app/backend/services/case_evidence_graph.py`
- `app/backend/services/case_intake_completeness.py`
- `app/backend/services/case_role_permission_matrix.py`
- `app/backend/services/case_workbench_payload.py`
- `app/backend/routers/case_workbench_runtime.py`
- `app/backend/services/case_workbench_persistence_plan.py`
- `app/backend/services/case_workbench_state_repository.py`
- `app/backend/services/case_workbench_runtime_binding.py`
- `app/backend/services/case_timeline_deadline_risk.py`
- `app/backend/services/case_team_access_policy.py`
- `app/backend/services/case_task_notification_policy.py`
- `app/backend/services/client_delivery_risk_checklist.py`
- `app/backend/services/client_delivery_transparency_policy.py`
- `app/backend/services/contract_clause_extraction_schema.py`
- `app/backend/services/deadline_validation_policy.py`
- `app/backend/services/document_delivery_package_manifest.py`
- `app/backend/services/document_version_diff_checklist.py`
- `app/backend/services/evidence_exhibit_package_policy.py`
- `app/backend/services/feedback_lifecycle_policy.py`
- `app/backend/services/gemini_newapi_cheap_first_policy.py`
- `app/backend/services/gemini_newapi_cheap_first_calibration.py`
- `app/backend/services/model_ops_gemini_cheap_first_route_preflight.py`
- `app/backend/tests/test_model_ops_gemini_cheap_first_route_preflight.py`
- `app/backend/services/route_telemetry_repository.py`
- `app/backend/services/legal_document_benchmark_fixtures.py`
- `app/backend/services/legal_rag_failure_fixtures.py`
- `app/backend/services/legal_source_ingestion_metadata.py`
- `app/backend/services/legal_source_freshness_policy.py`
- `app/backend/services/legal_source_durable_index_plan.py`
- `app/backend/services/legal_source_index_repository.py`
- `app/backend/services/legal_rag_index_binding.py`
- `app/backend/routers/legal_rag.py`
- `app/backend/services/lawyer_review_workflow_policy.py`
- `app/backend/services/maintenance_heartbeat_evidence.py`
- `app/backend/services/matter_audit_retention_policy.py`
- `app/backend/services/matter_intake_readiness_policy.py`
- `app/backend/services/model_default_recommendation_snapshot.py`
- `app/backend/services/model_default_candidate_selector.py`
- `app/backend/services/model_price_refresh_monitor.py`
- `app/backend/services/model_cost_regression_snapshots.py`
- `app/backend/services/route_telemetry_persistence_plan.py`
- `app/backend/services/ocr_import_readiness_policy.py`
- `app/backend/routers/deep_review.py`
- `app/backend/services/small_legal_document_corpus_expansion.py`
- `app/backend/services/legal_document_template_matrix.py`
- `app/backend/services/legal_document_benchmark_suite.py`
- `app/backend/services/legal_rag_request_metadata.py`
- `app/backend/routers/case_intelligence.py`
- `app/backend/services/case_intelligence.py`
- `app/backend/services/case_ai_workbench.py`
- `app/backend/services/legal_document_export_readiness.py`
- `app/backend/services/legal_external_research_digest.py`
- `app/backend/services/product_feature_gap_radar.py`
- `app/backend/tests/test_billing_entitlement_gap.py`
- `app/backend/tests/test_billing_usage_router.py`
- `app/backend/tests/test_billing_quota_migration_plan.py`
- `app/backend/tests/test_billing_quota_persistence_plan.py`
- `app/backend/tests/test_billing_quota_repository.py`
- `app/backend/tests/test_billing_entitlement_quota_binding.py`
- `app/backend/tests/test_billing_usage_quota_policy.py`
- `app/backend/tests/test_billing_payment_reconciliation.py`
- `app/backend/tests/test_generated_documents_quota.py`
- `app/backend/tests/test_case_evidence_graph.py`
- `app/backend/tests/test_case_intake_completeness.py`
- `app/backend/tests/test_case_role_permission_matrix.py`
- `app/backend/tests/test_case_workbench_payload.py`
- `app/backend/tests/test_case_workbench_runtime_router.py`
- `app/backend/tests/test_case_workbench_persistence_plan.py`
- `app/backend/tests/test_case_workbench_state_repository.py`
- `app/backend/tests/test_case_workbench_runtime_binding.py`
- `app/backend/tests/test_case_timeline_deadline_risk.py`
- `app/backend/tests/test_case_team_access_policy.py`
- `app/backend/tests/test_case_task_notification_policy.py`
- `app/backend/tests/test_client_delivery_risk_checklist.py`
- `app/backend/tests/test_client_delivery_transparency_policy.py`
- `app/backend/tests/test_contract_clause_extraction_schema.py`
- `app/backend/tests/test_deadline_validation_policy.py`
- `app/backend/tests/test_document_delivery_package_manifest.py`
- `app/backend/tests/test_document_version_diff_checklist.py`
- `app/backend/tests/test_evidence_exhibit_package_policy.py`
- `app/backend/tests/test_feedback_lifecycle_policy.py`
- `app/backend/tests/test_gemini_newapi_cheap_first_policy.py`
- `app/backend/tests/test_gemini_newapi_cheap_first_calibration.py`
- `app/backend/tests/test_route_telemetry_repository.py`
- `app/backend/tests/test_legal_document_benchmark_fixtures.py`
- `app/backend/tests/test_legal_rag_failure_fixtures.py`
- `app/backend/tests/test_legal_source_ingestion_metadata.py`
- `app/backend/tests/test_legal_source_freshness_policy.py`
- `app/backend/tests/test_legal_source_durable_index_plan.py`
- `app/backend/tests/test_legal_source_index_repository.py`
- `app/backend/tests/test_legal_rag_index_binding.py`
- `app/backend/tests/test_legal_rag_router.py`
- `app/backend/tests/test_lawyer_review_workflow_policy.py`
- `app/backend/tests/test_maintenance_heartbeat_evidence.py`
- `app/backend/tests/test_matter_audit_retention_policy.py`
- `app/backend/tests/test_matter_intake_readiness_policy.py`
- `app/backend/tests/test_model_default_recommendation_snapshot.py`
- `app/backend/tests/test_model_default_candidate_selector.py`
- `app/backend/tests/test_model_price_refresh_monitor.py`
- `app/backend/tests/test_model_cost_regression_snapshots.py`
- `app/backend/tests/test_route_telemetry_persistence_plan.py`
- `app/backend/tests/test_ocr_import_readiness_policy.py`
- `app/backend/tests/test_deep_review_ocr_readiness_runtime.py`
- `app/backend/tests/test_case_access_control.py`
- `app/backend/tests/test_case_permission_runtime_router.py`
- `app/backend/tests/test_small_legal_document_corpus_expansion.py`
- `app/backend/tests/test_legal_document_template_matrix.py`
- `app/backend/tests/test_legal_document_benchmark_suite.py`
- `app/backend/tests/test_legal_rag_request_metadata.py`
- `app/backend/tests/test_legal_document_export_readiness.py`
- `app/backend/tests/test_legal_external_research_digest.py`
- `app/backend/tests/test_product_feature_gap_radar.py`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/lib/billingUsageApi.ts`
- `app/frontend/src/lib/legalRagApi.ts`
- `app/frontend/src/lib/workbenchRuntimeApi.ts`
- `app/frontend/src/lib/caseApi.ts`
- `app/frontend/src/components/billing/BillingUsageBadge.tsx`
- `app/frontend/src/components/cases/CaseWorkbenchRuntimePanel.tsx`
- `app/frontend/src/components/cases/LegalRagResearchPanel.tsx`
- `app/frontend/src/components/Layout.tsx`
- `app/frontend/src/pages/CaseDetailPage.tsx`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/BILLING_ENTITLEMENT_GAP.md`
- `docs/BILLING_QUOTA_MIGRATION_PLAN.md`
- `docs/BILLING_QUOTA_PERSISTENCE_PLAN.md`
- `docs/BILLING_USAGE_QUOTA_POLICY.md`
- `docs/CASE_EVIDENCE_GRAPH.md`
- `docs/CASE_INTAKE_COMPLETENESS.md`
- `docs/CASE_ROLE_PERMISSION_MATRIX.md`
- `docs/CASE_ACCESS_CONTROL_RUNTIME_GATE.md`
- `docs/CASE_WORKBENCH_PAYLOAD.md`
- `docs/CASE_WORKBENCH_PERSISTENCE_PLAN.md`
- `docs/CASE_TIMELINE_DEADLINE_RISK.md`
- `docs/CASE_TEAM_ACCESS_POLICY.md`
- `docs/CASE_TASK_NOTIFICATION_POLICY.md`
- `docs/CLIENT_DELIVERY_RISK_CHECKLIST.md`
- `docs/CLIENT_DELIVERY_TRANSPARENCY_POLICY.md`
- `docs/CONTRACT_CLAUSE_EXTRACTION_SCHEMA.md`
- `docs/DEADLINE_VALIDATION_POLICY.md`
- `docs/DOCUMENT_DELIVERY_PACKAGE_MANIFEST.md`
- `docs/DOCUMENT_VERSION_DIFF_CHECKLIST.md`
- `docs/EVIDENCE_EXHIBIT_PACKAGE_POLICY.md`
- `docs/FEEDBACK_LIFECYCLE_POLICY.md`
- `docs/GEMINI_NEWAPI_CHEAP_FIRST_POLICY.md`
- `docs/GEMINI_NEWAPI_CHEAP_FIRST_CALIBRATION.md`
- `docs/LEGAL_RAG_FAILURE_FIXTURES.md`
- `docs/LEGAL_SOURCE_INGESTION_METADATA.md`
- `docs/LEGAL_SOURCE_FRESHNESS_POLICY.md`
- `docs/LEGAL_SOURCE_DURABLE_INDEX_PLAN.md`
- `docs/LAWYER_REVIEW_WORKFLOW_POLICY.md`
- `docs/MAINTENANCE_HEARTBEAT_EVIDENCE.md`
- `docs/MATTER_AUDIT_RETENTION_POLICY.md`
- `docs/MATTER_INTAKE_READINESS_POLICY.md`
- `docs/MODEL_DEFAULT_RECOMMENDATION_SNAPSHOT.md`
- `docs/MODEL_DEFAULT_CANDIDATE_SELECTOR.md`
- `docs/MODEL_PRICE_REFRESH_MONITOR.md`
- `docs/MODEL_COST_REGRESSION_SNAPSHOTS.md`
- `docs/ROUTE_TELEMETRY_PERSISTENCE_PLAN.md`
- `docs/OCR_IMPORT_READINESS_POLICY.md`
- `docs/LEGAL_DOCUMENT_BENCHMARK_FIXTURES.md`
- `docs/SMALL_LEGAL_DOCUMENT_CORPUS_EXPANSION.md`
- `docs/LEGAL_DOCUMENT_TEMPLATE_MATRIX.md`
- `docs/LEGAL_DOCUMENT_EXPORT_READINESS.md`
- `docs/LEGAL_EXTERNAL_RESEARCH_DIGEST.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`
- `docs/OSS_MAINTENANCE_EVIDENCE.md`
- `docs/USER_RESEARCH_AND_MAINTENANCE.md`
- `docs/RELEASE_READINESS.md`
