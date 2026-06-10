# Continuous Update Ledger

Current OSS maintenance route-plan research alignment slice:
`oss-maintenance-route-plan-research-alignment` binds the legal document
route-plan replay and research-alignment evidence into the OSS maintenance
profile, release-readiness controls, quality signal evidence paths, and
application guardrails. It makes the reviewer-facing maintenance endpoint show
cheap-first route planning, replay status, and stored Gemini/FrugalGPT/
LegalBench-RAG/LexEval source-alignment boundaries alongside other project
maintenance evidence. It does not call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, models, public datasets, or the network; download
papers or benchmark data; execute benchmark runs; change defaults; shift
traffic; write configuration; or return public benchmark text, raw fixture
snippets, generated document text, prompts, submitted scenario rationale,
scenario payloads, model outputs, gateway responses, emails, identifiers, or
credentials.

Current legal document benchmark route-plan research alignment slice:
`legal-document-benchmark-route-plan-research-alignment` maps the route-plan
replay scenarios to stored Gemini official model/pricing URLs, FrugalGPT
cheap-first cascade signals, LegalBench-RAG grounding signals, and LexEval
zh-CN legal task-family signals. It exposes source anchors, alignment rows,
linked replay status, release actions, and claim boundaries in the maintenance
UI before maintainers cite public research as evidence for local cheap-first
route planning. The endpoint is available at
`/api/v1/maintenance/legal-review-benchmark/document-route-plan/research-alignment`.
It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints,
models, public datasets, or the network; download papers or benchmark data;
execute benchmark runs; change defaults; shift traffic; write configuration; or
return public benchmark text, raw fixture snippets, generated document text,
prompts, submitted scenario rationale, model outputs, gateway responses, emails,
identifiers, or credentials.

Current legal document benchmark route-plan replay slice:
`legal-document-benchmark-route-plan-replay` adds deterministic metadata-only
scenario replay for the local legal-document benchmark route plan. It checks
default cheap-first routes, unapproved premium route-down behavior, simulated
approved premium blocking, and grounded legal-opinion routing before maintainers
trust the route plan for benchmark execution planning. The endpoint is
available at
`/api/v1/maintenance/legal-review-benchmark/document-route-plan/replay`.
It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints,
models, public datasets, or the network; execute benchmark runs; change
defaults; shift traffic; write configuration; or return raw fixture snippets,
generated document text, prompts, submitted scenario rationale, model outputs,
gateway responses, emails, identifiers, or credentials.

Current legal document benchmark route override UI slice:
`legal-document-benchmark-route-plan-override-ui` adds a maintenance-page
override preview for the local legal-document benchmark route plan. Maintainers
can choose a synthetic benchmark case, primary task, model id, and approval mode
to preview whether the cheap-first route plan blocks a premium default or routes
back to the recommended Gemini model before any benchmark execution or default
change. The UI only submits metadata under `case_route_overrides` and blocks
credential-shaped model input. It does not call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, models, public datasets, or the network; save route
overrides; change defaults; execute benchmark runs; return raw fixture snippets,
generated document text, prompts, payload bodies, model outputs, gateway
responses, headers, emails, identifiers, or credentials; or claim production
quality, public benchmark scores, legal advice, or default-promotion approval.

Current legal document benchmark route plan slice:
`legal-document-benchmark-route-plan` adds a metadata-only cheap-first route
plan for the local synthetic legal-document benchmark. It maps each benchmark
case to Flash-Lite prechecks, budgeted primary routes, Gemini catalog escalation
ladders, local cost estimates, and premium-default blocking before any
maintainer treats the benchmark as executable route evidence. The endpoint is
available at `/api/v1/maintenance/legal-review-benchmark/document-route-plan`.
It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints,
models, public datasets, or the network; change model defaults; execute
benchmark runs; return raw fixture snippets, generated document text, prompts,
payloads, model outputs, gateway responses, emails, identifiers, or
credentials; or claim public benchmark scores, production accuracy, legal
advice, real-client document coverage, or default-promotion approval.

Current legal benchmark default-promotion observation gate slice:
`modelops-legal-benchmark-default-promotion-observation-gate` adds a
metadata-only post-execution observation gate for cheap-first legal default
review. It turns external execution handoff rows into observation rows,
rollback-window rows, route telemetry checks, legal benchmark smoke checks, and
incident-status review before maintainers accept any post-change quality claim.
The endpoint is available at
`/api/v1/aihub/models/legal-benchmark-default-promotion-observation-gate`, the
aggregate ModelOps payload includes
`legal_benchmark_default_promotion_observation_gate`, and the evidence is
visible on `/model-ops` between the execution handoff and evidence handoff
sections. It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, public datasets, or the network; write configuration; write
env files; record approvals or signoffs; collect approver identity; execute
rollback; change defaults; shift traffic; return raw legal text, fixture
snippets, generated document text, prompts, payloads, model output, gateway
responses, emails, identifiers, or credentials; or claim post-change production
quality, public benchmark scores, legal advice, rollback execution, or
automatic default changes.

Current legal benchmark default-promotion execution handoff slice:
`modelops-legal-benchmark-default-promotion-execution-handoff` adds a
metadata-only execution handoff and rollback gate for cheap-first legal default
review. It turns externally signed signoff packet rows into execution
prerequisites, rollback gate items, config diff review checks, post-change
observation requirements, source status rows, and required execution roles
before maintainers perform any external legal-task Gemini default movement. The
endpoint is available at
`/api/v1/aihub/models/legal-benchmark-default-promotion-execution-handoff`, the
aggregate ModelOps payload includes
`legal_benchmark_default_promotion_execution_handoff`, and the evidence is
visible on `/model-ops` between the signoff packet and evidence handoff
sections. It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, public datasets, or the network; write configuration; write
env files; record approvals or signoffs; collect approver identity; execute
rollback; change defaults; shift traffic; return raw legal text, fixture
snippets, generated document text, prompts, payloads, model output, gateway
responses, emails, identifiers, or credentials; or claim maintainer approval,
public benchmark scores, production quality, legal advice, rollback execution,
or automatic default changes.

Current legal benchmark default-promotion signoff packet slice:
`modelops-legal-benchmark-default-promotion-signoff-packet` adds a
metadata-only signoff packet for cheap-first legal default review. It turns
checklist rows into external maintainer signoff requirements, pre-signoff
checks, source status rows, and required roles before maintainers consider any
legal-task Gemini default movement. The endpoint is available at
`/api/v1/aihub/models/legal-benchmark-default-promotion-signoff-packet`, the
aggregate ModelOps payload includes
`legal_benchmark_default_promotion_signoff_packet`, and the evidence is visible
on `/model-ops` between the checklist and evidence handoff sections. It does
not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models,
public datasets, or the network; write configuration; write env files; record
approvals or signoffs; collect approver identity; change defaults; shift
traffic; return raw legal text, fixture snippets, generated document text,
prompts, payloads, model output, gateway responses, emails, identifiers, or
credentials; or claim maintainer approval, public benchmark scores, production
quality, legal advice, or automatic default changes.

Current legal benchmark default-promotion checklist slice:
`modelops-legal-benchmark-default-promotion-checklist` adds a metadata-only
maintainer checklist for cheap-first legal default review. It joins the legal
benchmark default-promotion bridge, cheap-first release decision, and
default-change queue into source status rows and checklist rows before
maintainers consider any legal-task Gemini default movement. The endpoint is
available at
`/api/v1/aihub/models/legal-benchmark-default-promotion-checklist`, the
aggregate ModelOps payload includes
`legal_benchmark_default_promotion_checklist`, and the evidence is visible on
`/model-ops` between the default-promotion bridge and evidence handoff sections.
It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints,
models, public datasets, or the network; write configuration; write env files;
record approvals; change defaults; shift traffic; return raw legal text,
fixture snippets, generated document text, prompts, payloads, model output,
gateway responses, emails, identifiers, or credentials; or claim maintainer
approval, public benchmark scores, production quality, legal advice, or
automatic default changes.

Current legal benchmark default-promotion bridge slice:
`modelops-legal-benchmark-default-promotion-bridge` adds a metadata-only
ModelOps and release-decision bridge for cheap-first legal default review. It
joins legal fixture benchmark gate, default-promotion packet, regression
budget, evidence handoff, and Gemini official lifecycle drift gate into one
source row and promotion row packet before maintainers consider any legal-task
Gemini default movement. The endpoint is available at
`/api/v1/aihub/models/legal-benchmark-default-promotion-bridge`, the aggregate
ModelOps payload includes `legal_benchmark_default_promotion_bridge`, and the
evidence is visible on `/model-ops` between the regression budget and evidence
handoff sections. It does not call NewAPI, Gemini, OpenAI, Google, gateways,
app AI endpoints, models, public datasets, or the network; write configuration;
change defaults; shift traffic; return raw legal text, fixture snippets,
generated document text, prompts, payloads, model output, gateway responses,
emails, identifiers, or credentials; or claim maintainer approval, public
benchmark scores, production quality, legal advice, or automatic default
changes.

Current legal fixture cheap-first regression budget slice:
`modelops-legal-fixture-cheap-first-regression-budget` adds a metadata-only
ModelOps and release-decision signal for low-resource cheap-first legal fixture
reviews. It joins fixture regression comparison, cheap-first benchmark gate,
default-promotion packet, and small-document runbook status into one budget
with `max_parallel_requests=1`, fixture ids, source statuses, cost deltas,
reason codes, review actions, and explicit no-default-change/no-gateway
boundaries. The endpoint is available at
`/api/v1/aihub/models/legal-fixture-cheap-first-regression-budget`, the
aggregate ModelOps payload includes
`legal_fixture_cheap_first_regression_budget`, and the evidence is visible on
`/model-ops` between the default-promotion packet and evidence handoff. It does
not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models,
public datasets, or the network; write configuration; change defaults; shift
traffic; return raw legal text, fixture snippets, generated document text,
prompts, payloads, model output, gateway responses, emails, identifiers, or
credentials; or claim maintainer approval, production quality, legal advice, or
automatic default changes.

Current Gemini official cheap-first source review slice:
`modelops-gemini-official-cheap-first-source-review` adds metadata-only
ModelOps evidence for the cheapest Gemini text defaults. It compares local
catalog pricing for Gemini 2.5 Flash-Lite, Flash, and Pro, exposes Flash-Lite
input/output price ratios, checks high-frequency defaults remain Flash-Lite
aligned, and links source freshness/default-promotion blockers from the Gemini
catalog source audit. The endpoint is available at
`/api/v1/aihub/models/gemini-official-cheap-first-source-review`, the aggregate
ModelOps payload includes `gemini_official_cheap_first_source_review`, and the
evidence is visible on `/model-ops` between the catalog source audit and the
official model family roadmap. It does not call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, models, or the network; write configuration; change
defaults; shift traffic; return API keys, Authorization headers, request
bodies, response bodies, prompts, raw payloads, raw legal text, model outputs,
emails, identifiers, or credentials; or claim pricing accuracy, production
quality, account inventory, live gateway readiness, or automatic default
changes.

Current Gemini official lifecycle drift gate slice:
`modelops-gemini-official-lifecycle-drift-gate` adds metadata-only ModelOps
evidence between the official cheap-first source review and the official model
family roadmap. It checks that high-frequency cheap, fast, classification, and
OCR defaults remain on stable `gemini-2.5-flash-lite`, marks gateway-observed
Gemini/NewAPI names as review-only until lifecycle, pricing, and gateway
support are refreshed, blocks preview/deprecated/shutdown lifecycle labels from
defaults, and exposes local catalog lifecycle drift. The endpoint is available
at `/api/v1/aihub/models/gemini-official-lifecycle-drift-gate`, the aggregate
ModelOps payload includes `gemini_official_lifecycle_drift_gate`, and the
evidence is visible on `/model-ops` between the official cheap-first source
review and the official model family roadmap. It does not call NewAPI, Gemini,
OpenAI, Google, gateways, app AI endpoints, models, or the network; write
configuration; change defaults; shift traffic; return API keys, Authorization
headers, request bodies, response bodies, prompts, raw payloads, raw legal
text, model outputs, emails, identifiers, or credentials; or claim pricing
accuracy, live gateway execution, all Gemini model support, production quality,
or automatic default changes.

Current small legal document benchmark runbook evidence slice:
`small-legal-document-benchmark-runbook-evidence` adds a metadata-only
maintenance packet for low-resource legal-document delivery checks. It joins the
small corpus expansion, deterministic legal document benchmark suite,
fact-consistency benchmark, and final document delivery release gate into one
serial runbook with `max_parallel_requests=1`, review/block status rows,
source endpoint links, claim boundaries, and validation commands. The endpoint
is available at
`/api/v1/maintenance/legal-review-benchmark/small-document-runbook-evidence`
and the evidence is visible on `/maintenance` before the Legal RAG hallucination
triage gate. It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, public datasets, or the network; write configuration; change
defaults; shift traffic; return raw legal text, snippets, generated text,
prompts, payloads, model output, gateway responses, emails, identifiers, or
credentials; or claim public benchmark scores, production legal quality,
client-document coverage, final document generation, legal advice, or client
delivery.

Current route telemetry result archive slice:
`route-telemetry-result-archive` adds a metadata-only archive and cost ledger
for cheap-first route telemetry. The evidence joins the local route telemetry
repository, ops summary, triage queue, and remediation plan into daily archive
rows, task/model cost ledger rows, release-review links, ModelOps readiness,
release readiness, and the `/model-ops` UI. It does not call NewAPI, Gemini,
OpenAI, Google, gateways, app AI endpoints, models, or the network; write
configuration; change default routes; shift traffic; claim production health;
claim public benchmark scores; or return raw events, prompts, legal text,
request bodies, response bodies, headers, gateway responses, model outputs,
emails, identifiers, or credentials. Unknown or unpriced gateway models remain
unpriced and review-only.

Current ModelOps user-need Gemini route coverage slice:
`user-need-gemini-route-coverage` is now visible from `/model-ops` through
`/api/v1/aihub/models/user-need-gemini-route-coverage` in addition to the
maintenance evidence page. The slice keeps the route coverage evidence
metadata-only while showing high-priority Flash-Lite protection, linked Gemini
route tasks, review reasons, default-model status, and no-default-route-change
boundaries next to the ModelOps user-need release bridge and cheap-first
handoff controls. It does not call NewAPI, Gemini, OpenAI, Google, gateways,
app AI endpoints, models, public datasets, or the network; write
configuration; change default routes; shift traffic; or return raw legal text,
prompts, payloads, headers, model outputs, gateway responses, emails,
identifiers, or credentials.

Current ModelOps selector replay workbench slice:
`modelops-selector-replay-workbench` adds a metadata-only POST workbench to the
ModelOps Gemini/NewAPI selector replay panel. Reviewers can paste or reset a
small JSON scenario set, run the deterministic local replay endpoint, and see
the sanitized result replace the panel evidence without leaving ModelOps. The
slice binds the UI to `/api/v1/aihub/models/gemini-newapi-selector-replay`,
adds loading-gated evaluation and client-side sensitive-input rejection, and
extends release/ledger evidence with frontend typecheck and UI regression
commands. It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, or the network; write configuration; change defaults; shift
traffic; or return prompts, legal text, document bodies, request or response
bodies, transport metadata, model result text, emails, identifiers, or
credentials.

Current runtime catalog-safe default fallback slice:
`runtime-catalog-safe-default-fallback` adds runtime protection when text or
embedding task defaults drift to unknown gateway ids, preview/review lifecycle
models, unpriced catalog rows, or models above the task budget. The budget
policy keeps the configured value visible for operations evidence, while the
runtime router sends the actual AIHub request to the stable, priced,
within-budget catalog recommendation and labels the downgrade with
`unsafe_task_default_routed_to_recommended`. PDF and media exception routes are
unchanged. The evidence does not call NewAPI, Gemini, OpenAI, Google, gateways,
app AI endpoints, models, or the network; write configuration; change defaults;
shift traffic; or return prompts, legal text, payloads, model outputs, gateway
responses, headers, emails, identifiers, or credentials.

Current feedback benchmark release packet slice:
`feedback-user-need-legal-document-benchmark-release-packet` adds a
metadata-only bridge from feedback benchmark backlog rows into release-review
and customer-visible resolution gates. It joins privacy-safe feedback clusters,
feedback lifecycle checks, user-need implementation queue status,
legal-document benchmark evidence, and sanitized release observations without
returning raw feedback, customer notes, public resolution text, PII, uploaded
document text, fixture snippets, public benchmark text, prompts, payload
bodies, gateway responses, model outputs, or credentials. It does not claim
feedback resolution, customer notification, production legal quality, public
benchmark scores, or client-document coverage.

Current feedback benchmark backlog slice:
`feedback-user-need-legal-document-benchmark-backlog` adds a metadata-only
bridge from privacy-safe feedback clusters to roadmap user needs and
legal-document benchmark backlog rows. It ranks create-fixture, review, ready,
and blocked actions from feedback severity, mapped user-need priority, local
benchmark coverage, and legal-document evidence status. It is visible at
`/api/v1/maintenance/feedback/user-need-legal-document-benchmark-backlog` and
on the maintenance evidence page without returning raw feedback, PII, uploaded
document text, prompts, payload bodies, model outputs, gateway responses, or
credentials.

Current user-need legal-document evidence slice:
`user-need-legal-document-benchmark-evidence` adds a metadata-only bridge from
roadmap user needs to local legal-document benchmark evidence. It joins
user-need benchmark coverage, synthetic `ldoc-*` document cases, fact
consistency checks, local rule baseline status, and the cheap-first legal
fixture gate, and exposes the bridge at
`/api/v1/maintenance/user-needs/legal-document-benchmark-evidence` and the
`/maintenance` page. It does not download public datasets, import public
benchmark text, claim public benchmark scores or production legal quality, call
NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the
network; change default models; write configuration; shift traffic; or return
raw legal text, fixture snippets, document snippets, prompts, model outputs,
payload bodies, credentials, emails, or client material.

Current public benchmark fixture priority slice:
`legal-public-fixture-priority-queue` adds a metadata-only queue that turns
LawBench, LexEval, LegalBench, LegalBench-RAG, CUAD, LexGLUE, CaseGen, and
corpus-scale source metadata into the next synthetic legal-document fixture
work items. It joins the public sampler, fixture crosswalk, user-need benchmark
coverage, local legal-document rule baseline, and small-corpus metadata, and
exposes the queue at
`/api/v1/maintenance/legal-review-benchmark/public-fixture-priority-queue` and
the `/maintenance` page. It does not download datasets, import public benchmark
text, claim public benchmark scores, call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, models, or the network; write configuration; shift
traffic; or return raw legal text, fixture snippets, small-corpus excerpts,
prompts, model outputs, gateway payloads, credentials, emails, or client
material.

Current legal document local baseline slice:
`legal-document-local-rule-baseline-gate` adds a no-model local rule baseline
over the small synthetic Chinese legal-document fixtures, exposes it on the
maintenance page and
`/api/v1/maintenance/legal-review-benchmark/document-fixtures/local-baseline`,
and requires it inside the ModelOps legal fixture cheap-first benchmark gate
and default promotion packet before cheap-first Gemini/NewAPI default evidence
can be considered review-ready. It returns status, score, case ids, and match
counts only. It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, or the network; write configuration; shift traffic; or
return raw fixture snippets, local rule predictions, extracted field values,
prompts, generated document text, model outputs, gateway payloads,
credentials, emails, or client material.

Current ModelOps NewAPI channel bootstrap slice:
`modelops-newapi-channel-bootstrap` adds a metadata-only cheap-first setup
packet for NewAPI/YibuAPI/OpenAI-compatible Gemini channels. It normalizes bare
channel URLs such as `https://yibuapi.com` to `/v1`, represents supplied key
presence only as the `APP_AI_KEY` placeholder, joins gateway connection-profile
and runtime-configuration evidence with observed Gemini intake, coverage-gap,
and premium-exception review evidence, and exposes the packet through
`/api/v1/aihub/models/newapi-channel-bootstrap`, the aggregate
`/api/v1/aihub/models` payload, `/api/v1/maintenance/gemini/newapi-channel-bootstrap`,
`/model-ops`, and `/maintenance`. It does not call NewAPI, Gemini, OpenAI,
Google, yibuapi, gateways, app AI endpoints, models, or the network; write
`.env`, source configuration, default routes, or traffic; claim key validation
or live model inventory; or return raw payloads, prompts, legal text, model
outputs, gateway responses, Authorization headers, emails, identifiers, or
credentials.

Current ModelOps gateway probe runbook gate slice:
`model-gateway-probe-runbook-gate` adds a metadata-only ordered rollout gate
for NewAPI/Gemini gateway probes. It joins runtime/channel normalization,
secret-boundary verification, list-models evidence, cheap JSON probe status,
optional image smoke, small synthetic legal fixture smoke, and maintainer
default-change review into `/api/v1/aihub/models/gateway-probe-runbook-gate`
and the ModelOps page. It does not call NewAPI, Gemini, OpenAI, Google,
yibuapi, gateways, app AI endpoints, models, or the network; write
configuration; change defaults; shift traffic; or return raw probe payloads,
prompts, legal text, model outputs, gateway responses, headers, emails,
identifiers, or credentials.

Current ModelOps cheap-first cascade research slice:
`modelops-cheap-first-cascade-research-gate` adds a metadata-only gate that
links FrugalGPT-style cascade justification, official Gemini Flash-Lite
cheap-start positioning, local route quality budgets, escalation budgets,
failure-upgrade budgets, calibration evidence, and user-need handoff rows before
default model changes. It is exposed through
`/api/v1/aihub/models/cheap-first-cascade-research-gate` and the aggregate
`/api/v1/aihub/models` payload. It does not call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, public datasets, or the network; write
configuration; change default routes; shift traffic; claim public benchmark
scores; or return raw legal text, prompts, model outputs, payloads, headers,
emails, identifiers, or credentials.

Current ModelOps user-need handoff UI slice:
`modelops-user-need-cheap-first-handoff-ui` adds a read-only `/model-ops`
panel for the user-need cheap-first handoff. Maintainers can review
high-priority needs, cheap-first protected route counts, default-change
blockers, reviewer-only rows, source-section statuses, privacy/claim
boundaries, and row-level reviewer actions without leaving the ModelOps page.
It does not call models, gateways, app AI endpoints, or the network; write
configuration; change default routes; shift traffic; or return raw legal text,
benchmark samples, fixture snippets, prompts, payloads, headers, model outputs,
gateway responses, credentials, emails, or user identifiers.

Current ModelOps user-need cheap-first handoff slice:
`modelops-user-need-cheap-first-handoff` aggregates user-need benchmark
coverage, implementation queue rows, Gemini route coverage, and the user-need
release bridge into one reviewer handoff at
`/api/v1/aihub/models/user-need-cheap-first-handoff` and
`/api/v1/maintenance/user-needs/cheap-first-evidence-handoff`. It separates
blocking default-change rows from maintainer-review-only rows and shows which
high-priority needs are protected by cheap-first Gemini routes. It does not call
NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, public datasets, or
the network; download public datasets; import public benchmark samples; write
configuration; change default routes; shift traffic; claim public benchmark
scores; or return raw legal text, benchmark samples, fixture snippets, prompts,
model outputs, payloads, headers, emails, identifiers, or credentials.

Current Gemini media/speech review catalog slice:
`gemini-media-speech-review-catalog` adds review-only catalog coverage for Veo
3.1 video, Gemini TTS, and Gemini Live/native-audio candidates. It lets
OpenAI-compatible NewAPI/Gemini gateway model ids canonicalize into known
review rows, appear in the official family roadmap and Gemini variant matrix,
and remain blocked from high-frequency defaults until lifecycle, pricing, voice,
duration, route-shape, and gateway support are reviewed. Current
`APP_AI_VIDEO_MODEL`, `APP_AI_AUDIO_MODEL`, and `APP_AI_TRANSCRIPTION_MODEL`
defaults remain unchanged, and audio/video candidate pricing stays
explicit-review only. It does not call NewAPI, Gemini, OpenAI, Google, gateways,
app AI endpoints, models, or the network; write configuration; change defaults;
shift traffic; or return headers, request bodies, response bodies, prompts, raw
payloads, audio, transcripts, raw legal text, model outputs, gateway responses,
credentials, emails, or user identifiers.

Current Settings AI provider status slice:
`settings-ai-provider-status-card` adds a read-only Settings page status card
for OpenAI-compatible Gemini/NewAPI gateway readiness. It uses the existing
metadata-only runtime configuration API to show configured/missing provider
state, cheap-first role counts, safe environment variable names,
high-frequency Gemini defaults, recommended actions, and a link to the full
ModelOps evidence page. It does not call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, models, or the network; read admin settings; write
configuration; change defaults; shift traffic; or return raw gateway URLs,
credential values, Authorization headers, request bodies, response bodies,
prompts, raw legal text, model outputs, gateway responses, emails, or user
identifiers.

Current ModelOps gateway runtime configuration slice:
`model-gateway-runtime-configuration` adds metadata-only runtime setup evidence
for OpenAI-compatible NewAPI/YibuAPI/Gemini gateways. It verifies
`APP_AI_BASE_URL` normalization, `APP_AI_KEY` placeholder use, cheap-first
Gemini role defaults, and safe probe ordering before live gateway use, and
exposes the packet through
`/api/v1/aihub/models/gateway-runtime-configuration`. It does not call NewAPI,
Gemini, OpenAI, Google, yibuapi, gateways, app AI endpoints, models, or the
network; write `.env`, source configuration, default routes, or traffic; or
return API keys, Authorization headers, request bodies, response bodies,
prompts, raw legal text, model outputs, gateway responses, credentials, emails,
or user identifiers.

Current ModelOps user-need release slice:
`modelops-user-need-release-bridge` joins the user-need implementation priority
queue with Gemini cheap-first route coverage and exposes it through
`/api/v1/aihub/models/user-need-release-bridge`. High-priority implementation
or route blockers can block default changes; public benchmark license review,
premium exception review, partial coverage, route-hint calibration gaps, and
medium/low implementation gaps stay maintainer-review only. It does not call
NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, or the network;
download public datasets; import public benchmark samples; write configuration;
change default routes; shift traffic; or return raw legal text, prompts, route
payloads, request/response bodies, headers, model outputs, gateway responses,
credentials, emails, or user identifiers.

Current local dev dynamic proxy slice:
`local-dev-dynamic-proxy-port-guard` keeps the Vite development `/api` proxy
aligned with the backend port selected by `app/start_app_v2.sh`. The startup
script exports `VITE_API_PROXY_TARGET`, `VITE_BACKEND_PROXY_TARGET`, and
`VITE_PORT` before starting Vite, waits for `http://127.0.0.1:<frontend-port>/`
to answer, and prints the loopback frontend URL with the port. This reduces
local browser 500/proxy failures caused by opening bare `http://127.0.0.1/` or
by a stale hard-coded backend proxy target. It does not change business routes,
auth policy, model defaults, provider calls, traffic, raw request bodies, model
outputs, credentials, or user data.

Current ModelOps Gemini embedding slice:
`modelops-gemini-embedding-cheap-first-preflight` adds required metadata-only
embedding default evidence in the AIHub ModelOps payload and UI. It records
`APP_AI_EMBEDDING_MODEL=gemini-embedding-001`, `auto-embedding` alias coverage,
local catalog pricing, cheap-first embedding budget policy, and multimodal
`gemini-embedding-2` review routing. Text embeddings stay on
`gemini-embedding-001`; multimodal `gemini-embedding-2` remains review-required
before image, audio, video, PDF, or source-index use. It does not call
providers, gateways, app AI endpoints, models, or the network; write
configuration; change defaults; write indexes; shift traffic; or return source
text, raw legal text, source chunks, embedding vectors, request bodies, response
bodies, headers, prompts, raw payloads, model outputs, gateway responses,
emails, credentials, or user identifiers.

Current Legal RAG embedding readiness slice:
`legal-rag-embedding-readiness-gate` links the Gemini embedding cheap-first
preflight to Legal RAG index coverage and retrieval diagnostics in the
maintenance evidence API and UI. It records text-only `gemini-embedding-001`
readiness rows, keeps multimodal `gemini-embedding-2` review-required, exposes
index blockers before any embedding index write, and shows validation commands.
It does not call providers, gateways, app AI endpoints, models, or the network;
write indexes; download datasets; or return source ids, raw query, retrieved
context, legal text, source chunks, embedding vectors, prompts, model outputs,
gateway payloads, credentials, emails, or embedding/index/retrieval quality
claims.

Current Legal RAG embedding chunk policy slice:
`legal-rag-embedding-chunk-policy-gate` adds metadata-only chunk planning
evidence through `LegalRagEmbeddingChunkPolicyGateService` at
`/api/v1/maintenance/legal-rag-embedding-chunk-policy-gate`. It records
token-estimate chunk planning, source-type split strategies, overlap sizes,
citation-anchor checks, retrieval-locator blockers, freshness review
boundaries, laptop-safe chunk limits, and the default cheap embedding model
`gemini-embedding-001`. It does not call NewAPI, Gemini, models, gateways, app
AI endpoints, or the network; create embeddings; write indexes; download
datasets; or return source ids, raw query, raw retrieved context, raw legal
text, source chunks, embedding vectors, prompts, model outputs, gateway
payloads, credentials, emails, or chunk/embedding/index/retrieval quality
claims.

Current Legal RAG embedding index dry-run slice:
`legal-rag-embedding-index-dry-run-gate` adds metadata-only index manifest
review evidence through `LegalRagEmbeddingIndexDryRunGateService` at
`/api/v1/maintenance/legal-rag-embedding-index-dry-run-gate`. It turns
chunk-policy rows into dry-run manifest rows with planned vector-slot counts,
durable index persistence-field checks, repository-validation linkage, and
commit-action blockers before any embedding index write. It does not call
NewAPI, Gemini, models, gateways, app AI endpoints, or the network; create
embeddings; write indexes or databases; download datasets; or return source ids,
raw query, raw retrieved context, raw legal text, source chunks, embedding
vectors, prompts, model outputs, gateway payloads, credentials, emails, or
index/vector/retrieval quality claims.

Current Legal RAG embedding batch budget slice:
`legal-rag-embedding-batch-budget-gate` adds metadata-only cheap Gemini
embedding batch-budget evidence through
`LegalRagEmbeddingBatchBudgetGateService` at
`/api/v1/maintenance/legal-rag-embedding-batch-budget-gate`. It turns dry-run
manifest rows into planned batch counts, laptop-safe chunk and token limits,
local catalog batch-cost estimates, and release-action blockers before any
embedding run. It does not call NewAPI, Gemini, models, gateways, app AI
endpoints, or the network; create embeddings; write indexes or databases;
download datasets; or return source ids, raw query, raw retrieved context, raw
legal text, source chunks, embedding vectors, prompts, model outputs, gateway
payloads, credentials, emails, live pricing claims, or embedding/index/retrieval
quality claims.

Current Legal RAG embedding batch approval slice:
`legal-rag-embedding-batch-approval-packet` adds metadata-only maintainer review
evidence through `LegalRagEmbeddingBatchApprovalPacketService` at
`/api/v1/maintenance/legal-rag-embedding-batch-approval-packet`. It converts
batch-budget rows into serial low-resource queue order,
`max_parallel_embedding_requests=1`, required maintainer/RAG-index reviewer
roles, pre-approval checks, and advance/hold/block actions before any embedding
run. It does not claim approval, collect approver identity, write approval
records, call NewAPI, Gemini, models, gateways, app AI endpoints, or the
network; create embeddings; write indexes or databases; download datasets; or
return source ids, raw query, raw retrieved context, raw legal text, source
chunks, embedding vectors, prompts, model outputs, gateway payloads,
credentials, emails, live pricing claims, or embedding/index/retrieval quality
claims.

Current Legal RAG embedding batch observation slice:
`legal-rag-embedding-batch-observation-gate` adds metadata-only aggregate
observation evidence through `LegalRagEmbeddingBatchObservationGateService` at
`/api/v1/maintenance/legal-rag-embedding-batch-observation-gate`. It reviews
sanitized observed batch/chunk/vector-slot/token counts, cost deltas,
`max_parallel_embedding_requests=1`, and allow/hold/block index-review actions
after an external embedding run. It does not claim maintainer approval, execute
embeddings, call NewAPI, Gemini, models, gateways, app AI endpoints, or the
network; create embeddings; write indexes or databases; collect approver
identity; download datasets; or return source ids, approval item ids, raw
query, raw retrieved context, raw legal text, source chunks, embedding vectors,
prompts, model outputs, gateway payloads, credentials, emails, live pricing
claims, or embedding/index/retrieval quality claims.

Current Legal RAG embedding index commit review slice:
`legal-rag-embedding-index-commit-review-packet` adds metadata-only maintainer
review evidence through `LegalRagEmbeddingIndexCommitReviewPacketService` at
`/api/v1/maintenance/legal-rag-embedding-index-commit-review-packet`. It
converts ready aggregate observations into commit-review items with vector-slot
match evidence, observed chunk/cost evidence, required maintainer/RAG-index/
privacy signoffs, pre-commit checks, and prepare/hold/block actions before any
real index commit. It does not claim commit approval, execute embeddings, call
NewAPI, Gemini, models, gateways, app AI endpoints, or the network; write
indexes, databases, or commit records; collect committer identity; download
datasets; or return source ids, approval item ids, raw query, raw retrieved
context, raw legal text, source chunks, embedding vectors, prompts, model
outputs, gateway payloads, credentials, emails, live pricing claims, or
embedding/index/retrieval quality claims.

Current Legal RAG embedding index post-commit verification slice:
`legal-rag-embedding-index-post-commit-verification-gate` adds metadata-only
post-commit verification evidence through
`LegalRagEmbeddingIndexPostCommitVerificationGateService` at
`/api/v1/maintenance/legal-rag-embedding-index-post-commit-verification-gate`.
It converts commit-review rows and sanitized post-commit observations into
verification rows with expected/observed vector-slot counts, index entry
counts, metadata records, retrieval locators, checksum records, failed-entry
totals, rollback signals, and allow/hold/block retrieval-diagnostics review
actions. It does not claim commit approval, execute embeddings, call NewAPI,
Gemini, models, gateways, app AI endpoints, or the network; write indexes,
databases, or commit records; enable production retrieval; collect committer
identity; download datasets; or return source ids, approval item ids, raw
query, raw retrieved context, raw legal text, source chunks, embedding vectors,
prompts, model outputs, gateway payloads, credentials, emails, live pricing
claims, or embedding/index/retrieval quality claims.

Current Legal RAG embedding retrieval diagnostics handoff slice:
`legal-rag-embedding-retrieval-diagnostics-handoff-gate` adds metadata-only
handoff evidence through
`LegalRagEmbeddingRetrievalDiagnosticsHandoffGateService` at
`/api/v1/maintenance/legal-rag-embedding-retrieval-diagnostics-handoff-gate`.
It converts post-commit verification rows into ready, hold, and blocked
handoff rows with safe handoff payload fields, diagnostics-review-only
actions, rollback review links, and production-retrieval false flags. It does
not execute retrieval diagnostics, enable production retrieval, claim index or
retrieval quality, execute embeddings, call NewAPI, Gemini, models, gateways,
app AI endpoints, or the network; write indexes, databases, or commit records;
collect committer identity; download datasets; or return source ids, raw
query, user questions, retrieved context, raw legal text, source chunks,
embedding vectors, prompts, model outputs, gateway payloads, credentials,
emails, live pricing claims, legal advice, or client delivery claims.

Current ModelOps official Gemini roadmap slice:
`modelops-gemini-official-model-family-roadmap-evidence` exposes
metadata-only official Gemini family coverage evidence in the AIHub ModelOps
payload and UI. It keeps stable Gemini 2.5 Flash-Lite cheap-first text defaults
separate from the refreshed Gemini 3.5/3.1 catalog rows, Gemini 3 review rows,
explicit image rows, and Live/audio, embedding, and TTS roadmap gaps. It does not call providers, gateways, app AI
endpoints, models, or the network; write configuration; change defaults; or
return request bodies, response bodies, headers, prompts, raw payloads, legal
text, model outputs, emails, credentials, or user identifiers.

Current legal document fixture UI slice:
`legal-document-benchmark-fixture-ui` exposes the local synthetic legal-document
fixture suite and empty-prediction evaluator on the maintenance evidence page.
It shows readable zh-CN case ids, document types, expected-check counts, field
keys, snippet lengths, scoring state, local resource policy, validation
commands, and mojibake regression coverage while deliberately not rendering raw
fixture snippets, prompts, model responses, gateway payloads, credentials,
emails, or client material.

Current ModelOps source freshness slice:
`modelops-catalog-source-freshness-gate` extends the Gemini catalog source
audit with official pricing/model source review freshness, stale-source counts,
default-promotion source blocks, ModelOps UI visibility, release readiness
wording, and local regression checks. It remains metadata-only: it does not call
Google, Gemini, NewAPI, OpenAI, gateways, app AI endpoints, or the network, and
it does not include prompts, payloads, legal text, model outputs, credentials,
emails, gateway responses, or real environment values.

Current Legal RAG index coverage slice:
`legal-rag-index-coverage-gate` exposes a metadata-only index binding coverage
gate in the maintenance evidence API and UI. It reviews index plan rows, filter
validation, source coverage, locator coverage, jurisdiction/freshness gaps,
missing or stale source counts, forbidden filters, and cheap-first actions
without calling models, gateways, NewAPI, Gemini, or the network; it does not
download datasets or return source ids, raw query, retrieved context, legal
text, prompts, model outputs, gateway payloads, credentials, or index-quality
claims.

Current Legal RAG retrieval observation UI slice:
`legal-rag-retrieval-observation-ui-binding` exposes the metadata-only
retrieval observation gate in the maintenance evidence page with a typed POST
helper, sanitized sample payload, status/release distributions,
source-validation counts, cheap-first action review, and explicit
privacy/claim boundaries. It does not call models, gateways, NewAPI, Gemini, or
the network; it does not download datasets or return source ids, raw query,
retrieved context, legal text, prompts, model outputs, gateway payloads, or
credentials.

Current Legal RAG answer release readiness slice:
`legal-rag-answer-release-readiness-gate` exposes metadata-only answer-release
readiness through `LegalRagAnswerReleaseReadinessGateService` at
`/api/v1/maintenance/legal-rag-answer-release-readiness-gate`. It converts
sanitized retrieval observation rows into ready, review-required, and blocked
answer-release rows with internal draft actions, citation packet requirements,
lawyer-review requirements, cheap-first verify/escalate boundaries, and
client-delivery false flags. It does not call models, gateways, NewAPI, Gemini,
or the network; write answers; send client delivery; claim legal advice or
answer quality; download datasets; or return source ids, raw query, user
questions, retrieved context, legal text, prompts, model outputs, gateway
payloads, credentials, emails, or client material.

Current ModelOps first-paint slice:
`modelops-first-paint-aggregate-binding` lets the `/model-ops` browser page
render as soon as the aggregate `/api/v1/aihub/models` payload returns, then
keeps narrower evidence endpoints as missing-signal or aggregate-failure
fallbacks. This avoids long local 127.0.0.1 blank/default states while preserving legal fixture
cheap-first gate and default promotion packet evidence boundaries: no raw legal
text, prompts, payloads, model outputs, credentials, emails, provider calls,
gateway calls, configuration writes, or traffic shifts.

Current ModelOps UI binding slice:
`modelops-legal-fixture-modelops-ui-binding` exposes the legal fixture
cheap-first benchmark gate and default promotion packet through AIHub ModelOps
payloads, direct ModelOps endpoints, TypeScript helpers, and ModelOps main-page
panels. The panels show linked calibration task IDs, calibration decisions,
document benchmark samples, promotion evidence, and default-change boundaries
without raw legal text, prompts, request/response bodies, calibration payloads,
model outputs, credentials, emails, gateway calls, or traffic shifts.

Current ModelOps legal-fixture calibration slice:
`modelops-legal-fixture-cheap-first-calibration-binding` links the legal fixture
cheap-first benchmark gate and default promotion packet to Gemini/NewAPI
cheap-first calibration evidence. Gate and promotion rows now show linked
calibration task IDs, status, release gates, and decisions, and the maintenance
page uses limited-concurrency evidence loading plus a legacy `/maintenance/evidence`
alias so stale local links do not surface as a broken maintenance page.

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

Local dev stability slice: `local-dev-reload-stability-guard` hardens
`start_app_v2.sh` so backend reload watches exclude logs, pycache, pytest cache,
and test-output churn. This keeps the Vite proxy at `127.0.0.1:3000` from
falling into connection-refused or browser 500 loops while local tests are
running, without changing business routes, auth policy, provider calls, model
defaults, traffic, request bodies, model outputs, or credentials.

Feedback roadmap routing slice:
`feedback-roadmap-cheap-first-route-coverage` links the
`feedback-to-roadmap-loop` user need to a lowest-tier Gemini classification
calibration task and FrugalGPT cost-quality mapping. The route row now becomes
review-required instead of blocked while staying metadata-only: no public
dataset downloads, benchmark imports, provider/gateway/network calls,
configuration writes, default-route changes, traffic shifts, raw feedback text,
prompts, payloads, model outputs, credentials, emails, or user identifiers.

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

Current Legal RAG export slice: `legal-rag-export-readiness-packet` adds a
metadata-only review packet that joins selected-source binding, case export
readiness, and the deep-review export route gate into one export action. It
does not return raw reports, legal text, document text, user claims, PII,
prompts, model outputs, credentials, or call NewAPI, Gemini, gateways, or the
network.

Current model-ops slice: `model-price-refresh-monitor-readiness-ui` wires the
Gemini/NewAPI price refresh monitor into `/api/v1/aihub/models`, model-ops
readiness, and the `/model-ops` reviewer page. Unknown, preview, premium, or
unpriced gateway models now surface as release-review evidence before they can
be treated as cheap-first defaults.

Newest model-ops readiness slice:
`model-ops-default-recommendation-readiness-binding` promotes
`default_recommendation_snapshot` into the required ModelOps readiness
component table, adds role-level blocking/warning ids to the snapshot, and
shows the default-recommendation requirement on `/model-ops`. It does not call
gateways, write configuration, shift traffic, or expose prompts, raw payloads,
model outputs, legal text, credentials, emails, or user identifiers.

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
cheap-first eligibility, default-promotion block/review/ready state, promotion
safety checks, cheap-first candidate summaries, and maintainer runbook steps
only. Unknown Gemini-like rows block default promotion, review-only rows stay
outside default queues, and ready Flash-Lite-style candidates must still pass
selector replay, catalog impact replay, default-change queue, canary, approval,
rollback, and maintainer checklist evidence before any configuration edit. It
does not call NewAPI, Gemini, OpenAI, Google, gateways, or the network, write
real environment values, shift traffic, or include raw prompts, payloads, model
outputs, legal text, emails, or credentials.

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
preflight evidence and POST review form coverage for official source refresh
notes, local Gemini task defaults, observed model id metadata, variant review
states, alias capability coverage, and cheap-first coverage-gate status. It
keeps high-frequency work on stable Flash-Lite routes while preview, premium,
media, unknown, unpriced, or retired variants remain review/explicit-only. It
does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, or
the network, write configuration, shift traffic, claim live model quality, or
include request/response bodies, headers, prompts, raw payloads, legal text,
model outputs, gateway responses, credentials, emails, or user identifiers.

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

Current runtime explicit model fit evidence:
`modelops-runtime-explicit-model-fit-gate` adds shipped metadata-only runtime
route evidence for sanitized explicit task/model scenarios. It exposes unknown
gateway guards, reviewed gateway pass-through exceptions, explicit over-budget
exceptions, local downgrade enforcement, cheap-first alignment, observed gateway
fit review states, and privacy/claim boundaries without live gateway calls,
model calls, account inventory validation, configuration writes, default
changes, traffic shifts, API keys, Authorization headers, request bodies,
response bodies, headers, messages, prompts, raw payloads, legal text, model
outputs, gateway responses, credentials, emails, or user identifiers.

Current request execution preflight evidence:
`modelops-request-execution-preflight` adds shipped metadata-only per-request
execution evidence for sanitized NewAPI/Gemini runtime metadata. It joins local
runtime routing, cheap-first task ladders, fallback ordering, estimated token
cost, request cost bounds, and ModelOps UI review so maintainers can see which
requests are ready, review-required, locally downgraded, or blocked before live
calls. It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, or the network, write configuration, shift traffic, or
include headers, request bodies, prompts, messages, raw payloads, legal text,
model outputs, gateway responses, emails, user identifiers, or credentials.

Current request execution observation evidence:
`modelops-request-execution-observation-gate` adds shipped metadata-only
post-run request observation evidence for sanitized NewAPI/Gemini execution
metadata. It compares observed model ids, coarse status categories, fallback
use, token/cost/latency metadata, and local downgrade follow-through with
preflight rows so maintainers can see cheap-first drift and review exceptions
after dry runs or live calls. It does not call providers, gateways, app AI
endpoints, models, or the network, execute requests, write configuration,
change defaults, shift traffic, or include headers, request bodies, messages,
prompts, raw legal text, raw payloads, gateway responses, model outputs,
emails, user identifiers, or credentials.

Current request execution release-readiness binding:
`modelops-request-execution-release-readiness-binding` promotes the request
execution preflight into required release-readiness evidence. Release candidates
must now explicitly validate sanitized per-request Gemini/NewAPI routing,
cheap-first fallback order, token-cost estimates, task cost bounds,
`max_tokens` policy, and local downgrade visibility before live-call claims. It
does not call providers, gateways, models, app AI endpoints, or the network,
write configuration, change defaults, shift traffic, or include headers,
request bodies, messages, prompts, raw legal text, raw payloads, model outputs,
gateway responses, emails, user identifiers, or credentials.

Current runtime explicit unknown/lifecycle guard evidence:
`model-runtime-explicit-unknown-lifecycle-guard` changes local routing so
explicit unknown gateway models and non-stable preview/review lifecycle catalog
models route to stable task recommendations by default. Reviewed exceptions
must set `allow_over_budget_model=true` and remain visible through route reason
codes and route telemetry without live gateway calls, model calls, default
changes, configuration writes, prompts, raw legal text, API keys, Authorization
headers, gateway responses, or credentials.

Current AIHub endpoint route coverage evidence:
`modelops-aihub-endpoint-route-coverage-gate` adds shipped metadata-only
endpoint route coverage evidence for text, streaming text, PDF, embeddings,
image, video, audio, and transcription AIHub routes. It shows runtime-router coverage,
budget-decision coverage, route telemetry coverage, response route-payload
coverage, and media/speech/embedding catalog review gaps without calling NewAPI, Gemini, OpenAI,
Google, gateways, app AI endpoints, models, or the network, writing
configuration, shifting traffic, or including request/response bodies, headers,
prompts, raw payloads, legal text, model outputs, gateway responses,
credentials, emails, or user identifiers.

Current AIHub embedding runtime evidence:
`aihub-embedding-runtime` adds `POST /api/v1/aihub/embeddings` and
`AIHubService.embed_text` for cheap-first Legal RAG text embeddings. It routes
through `gemini-embedding-001`, records sanitized usage and route telemetry, and
returns route metadata plus numeric vectors without echoing source text,
persisting vectors in telemetry, writing indexes, changing defaults, or
returning credentials, headers, raw prompts, legal text, model outputs, or
gateway payloads.

`legal-rag-embedding-batch-preflight` adds
`POST /api/v1/legal-rag/embedding-batch-preflight` and the matching
maintenance endpoint for local input audit before any executable embedding
preview. It hashes chunk ids and text, estimates cheap-first Gemini embedding
tokens and catalog cost, and flags duplicate chunks, PII signals, preview-size
overages, and secret-like inputs without calling NewAPI, Gemini, models,
gateways, or the network; creating embeddings; writing indexes or databases; or
returning source text, source ids, sensitive values, embedding vectors, prompts,
gateway payloads, model outputs, or credentials.

`legal-rag-embedding-batch-preflight-ui-binding` adds the maintenance-page
review surface for that preflight. It exposes typed maintenance API bindings,
sample evaluation, preflight row/status distributions, duplicate-hash and PII
signal totals, hashed identifiers, local cost/token summaries, input-contract
flags, privacy boundaries, and validation commands with static UI regression
coverage. It does not render source text, source ids, sensitive values,
embedding vectors, prompts, gateway payloads, model outputs, credentials, or
legal advice claims.

`legal-rag-embedding-batch-preview-runtime` adds
`POST /api/v1/legal-rag/embedding-batch-preview` and
`LegalRagEmbeddingBatchPreviewService`. It lets maintainers run a small
cheap-first embedding smoke check through AIHub while returning only sanitized
hashes, dimensions, norms, vector checksums, usage units, and route metadata. It
does not write indexes or databases and does not return source text, source ids,
embedding vectors, prompts, gateway payloads, model outputs, or credentials.

Current AIHub media/speech default catalog evidence:
`modelops-aihub-media-speech-default-catalog-gate` adds shipped required
metadata-only release evidence at
`/api/v1/aihub/models/aihub-media-speech-default-catalog-gate`. It reviews
image, video, audio, transcription, future Live audio, and embedding default
coverage against endpoint route coverage, local catalog status, explicit
media/speech budget modes, official Gemini/Veo/TTS source anchors, default
release actions, and review items. Non-catalog and future-route defaults remain
explicit-review only without NewAPI, Gemini, OpenAI, Google, gateway, app-AI,
model, or network calls, configuration writes, default changes, traffic shifts,
request/response bodies, headers, prompts, raw payloads, audio, transcripts,
legal text, model outputs, gateway responses, credentials, emails, or user
identifiers.

Current AIHub media runtime compatibility evidence:
`modelops-aihub-media-runtime-compatibility-gate` adds shipped required
metadata-only release evidence at
`/api/v1/aihub/models/aihub-media-runtime-compatibility-gate`. It separates
current OpenAI-compatible `client.videos.create`/`retrieve`,
`client.audio.speech.create`, and `client.audio.transcriptions.create` code
paths from native Gemini/Veo/TTS/Live runtime requirements so Veo, Gemini TTS,
Gemini audio-understanding, and Live audio promotion remain review-only until
gateway shape, native adapter, polling, session, and output-extraction evidence
is attached. It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, or the network, write configuration, change defaults, shift
traffic, or include request/response bodies, headers, prompts, raw payloads,
audio, transcripts, legal text, model outputs, gateway responses, credentials,
emails, or user identifiers.

Current AIHub media/speech runtime routing evidence:
`aihub-media-speech-runtime-routing` adds shipped runtime routing for video,
audio, and transcription AIHub routes. The endpoints now use explicit
media/speech budget tasks, record sanitized route telemetry, return route
payload metadata where the response shape allows it, and keep non-catalog
gateway defaults review-only until pricing, lifecycle, and gateway behavior are
documented.

Current AIHub route-payload usage evidence:
`aihub-route-payload-usage-units` adds sanitized route payload metadata to PDF
analysis and image generation responses, adds task inference response coverage,
and exposes media usage units for image, video, audio, and transcription routes
in ModelOps. It does not call providers, gateways, NewAPI, Gemini, OpenAI, or
Google, and does not include prompts, PDF bytes, image bytes, audio,
transcripts, output URLs, raw payloads, request/response bodies, headers, model
outputs, credentials, emails, or user identifiers.

Current gentxt routing guard evidence:
`gentxt-routing-media-guard` adds metadata-only evidence that media and speech
routing labels are rejected for the text endpoint and remain scoped to media
endpoints. It adds service integration coverage that gentxt does not call media
default models, and surfaces guard counts and aliases in ModelOps without
calling NewAPI, Gemini, OpenAI, Google, providers, gateways, app AI endpoints,
models, or the network. It does not write configuration, shift traffic, or
include request/response bodies, headers, prompts, raw payloads, legal text,
model outputs, gateway responses, credentials, emails, or user identifiers.

Current gentxt stream route metadata evidence:
`gentxt-stream-route-metadata` adds a metadata-first SSE event for gentxt
streaming responses, closes the AIHub stream route payload and task inference
coverage gap, and preserves the legacy content-only service wrapper for
internal callers. It updates ModelOps coverage counts without calling NewAPI,
Gemini, OpenAI, Google, providers, gateways, app AI endpoints, models, or the
network, and without writing configuration, shifting traffic, or including
request/response bodies, headers, prompts, raw payloads, legal text, model
outputs, gateway responses, credentials, emails, or user identifiers.

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
gates, unsafe configured task defaults, and explicit reviewed overrides. The
repository persists only sanitized
reason-code lists and aggregate counts, and the ModelOps table shows those
counts without storing prompts, legal text, model outputs, payloads, emails, or
credentials.

Current route telemetry reason-code hotspot evidence:
`route-telemetry-reason-code-hotspots` turns sanitized aggregate
`reason_code_counts` into ops summary top reason codes, daily hotspot rows, and
triage actions for `over_task_budget`, `operator_review_required`,
`unknown_catalog_model`, `unknown_gateway_routed_to_recommended`,
`non_stable_model_routed_to_recommended`, allow-gated `gateway_passthrough`, and
`unknown_reason_code`.
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

Current legal fixture cheap-first regression budget evidence:
`modelops-legal-fixture-cheap-first-regression-budget` adds shipped
metadata-only low-resource regression budget evidence for legal fixture default
reviews. It records fixture ids, source statuses, regression deltas, cost
deltas, reason codes, and review actions only while feeding the cheap-first
release decision and ModelOps readiness. It does not call NewAPI, Gemini,
OpenAI, Google, gateways, public datasets, or the network, write configuration,
shift traffic, claim approval, or return raw legal text, fixture snippets,
generated document text, prompts, model outputs, credentials, or emails.

Current legal fixture evidence handoff:
`modelops-legal-fixture-evidence-handoff` adds an archive-safe metadata-only
handoff across local-run-review, cheap-first benchmark gate, default-promotion
packet, and continuous-session-run-monitor summaries. It exposes source
statuses, fixture counts, readiness/review/blocker counts, endpoint links, and
privacy/claim boundaries only. It does not return raw run reports,
observations, output text, gateway responses, prompts, messages, headers,
credentials, raw legal text, model outputs, external-provider results,
configuration writes, default changes, traffic shifts, 24-hour completion
claims, 100-update completion claims, GitHub push claims, or default-change
claims.

Current cheap-first release legal benchmark binding evidence:
`modelops-cheap-first-release-legal-benchmark-binding` binds the legal fixture
benchmark gate, legal fixture default-promotion packet, and legal benchmark
risk bridge into the cheap-first release decision. Failed fixture, document,
fact-consistency, calibration, or route-risk evidence blocks legal-task default
promotion; not-run, not-ready, public benchmark license review, premium
exception, and route watchlist evidence stays maintainer-review-only. It does
not write configuration, shift traffic, call model providers or gateways,
download public datasets, or include raw legal text, benchmark samples, prompts,
model outputs, credentials, or emails.

Current cheap-first release maintenance evidence panel:
`modelops-cheap-first-release-maintenance-evidence-panel` surfaces the
cheap-first release decision directly in the maintenance evidence page between
the legal fixture default-promotion packet and the legal route-risk queue. It
shows required signal counts, legal source checks, maintainer-review state,
default-promotion blockers, legal fixture policy, legal benchmark policy, and
privacy/claim boundaries without writing configuration, changing defaults,
shifting traffic, calling providers or gateways, downloading public datasets, or
including raw legal text, benchmark samples, prompts, model outputs, payloads,
credentials, or emails.

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
- `low_resource_fixture_evidence`: archive-safe local fixture evidence status, including optional regression-comparison metadata when supplied.
- `low_resource_test_policy`: fixture limits, serial execution policy, default benchmark endpoint, ledger review endpoint, and run-monitor review endpoint.
- `validation_commands`: small pytest commands that can run on a local laptop.

Current low-resource fixture regression evidence:
`legal-fixture-regression-comparison` now feeds the ledger's
`low_resource_fixture_evidence` summary when `low_resource_fixture_regression`
is posted. The ledger records only comparison status, release decision,
compared fixture count, regressed/newly-blocking/resolved counts, cost delta,
safe fixture ids, and dropped raw-field counts. It keeps raw model outputs,
gateway responses, prompts, legal text, client documents, request/response
bodies, headers, emails, credentials, and secrets out of the ledger response,
and it never mutates the 24-hour or 100-update completion flags.

Current case workbench runtime evidence:
`case-workbench-risk-refresh-plan` adds shipped metadata-only risk/evidence
refresh planning to repository-backed workbench payloads. It reads sanitized
section counts and event deltas, lists section/event ids that need follow-up,
and keeps live risk-state writes, evidence graph refreshes, notifications, raw
event payloads, legal text, and client contact details outside the ledger claim.

`case-workbench-risk-state-badges` adds shipped metadata-only badge projection
on top of the same runtime payload. The frontend runtime panel can show
critical, warning, watch, and ready badges for task blockers, urgent deadlines,
evidence gaps, and runtime-event deltas without writing risk state, refreshing
evidence graphs, sending notifications, or exposing raw matter content.

Current Legal RAG benchmark evidence:
`legal-rag-benchmark-alignment` adds a shipped metadata-only scorecard that maps
LegalBench-RAG, CRAG, RAGAS, and Legal RAG Bench signals to local retrieval
diagnostics, abstention escalation, public-source sampling policy, fixture
crosswalk coverage, and cheap-first Gemini/NewAPI boundaries. It blocks public
benchmark, retrieval-quality, and legal-answer claims when local fixture or
retrieval evidence has gaps, and it does not call models, gateways, NewAPI,
Gemini, the network, or return public benchmark text, raw queries, retrieved
context, raw legal text, prompts, model outputs, or credentials.

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
- `docs/MODELOPS_GEMINI_OFFICIAL_MODEL_FAMILY_ROADMAP.md`
- `docs/LEGAL_RAG_EMBEDDING_CHUNK_POLICY_GATE.md`
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
- `app/backend/services/model_ops_gemini_official_model_family_roadmap.py`
- `app/backend/tests/test_model_ops_gemini_official_model_family_roadmap.py`
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
