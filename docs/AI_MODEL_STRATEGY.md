# AI Model Strategy

本项目通过 OpenAI-compatible 网关访问模型，目标是优先降低高频流程成本，同时保留复杂法律审查所需的高级模型能力。真实 API key 只允许放在本地 `app/backend/.env` 或部署平台的 Secret 中，不得提交到 Git。

## Gateway Setup

后端统一从 `app/backend/core/config.py` 读取网关配置：

```env
APP_AI_BASE_URL=https://yibuapi.com/v1
APP_AI_KEY=replace-with-your-key
APP_AI_CHEAP_MODEL=gemini-2.5-flash-lite
APP_AI_BALANCED_MODEL=gemini-2.5-flash
APP_AI_PREMIUM_MODEL=gemini-2.5-pro
APP_OCR_MODEL=gemini-2.5-flash-lite
APP_AI_FAST_MODEL=gemini-2.5-flash-lite
APP_AI_CLASSIFIER_MODEL=gemini-2.5-flash-lite
APP_AI_AGENTIC_MODEL=gemini-3.1-flash-lite
APP_AI_GROUNDED_RESEARCH_MODEL=gemini-3.1-flash-lite
APP_AI_REVIEW_MODEL=gemini-2.5-flash
APP_AI_PDF_MODEL=gemini-2.5-pro
APP_AI_IMAGE_MODEL=gemini-2.5-flash-image
APP_AI_VIDEO_MODEL=wan2.6-t2v
APP_AI_AUDIO_MODEL=qwen3-tts-flash
APP_AI_TRANSCRIPTION_MODEL=scribe_v2
APP_AI_PREMIUM_REQUIRES_REVIEW=true
```

New API 文档说明，客户端可把平台地址配置为 OpenAI SDK 的 `base_url`，并把平台令牌作为 `api_key` 使用。Google Gemini 官方文档也说明 Gemini 模型可用 OpenAI libraries 和 REST API 访问，只需设置 Gemini/OpenAI-compatible base URL、API key 和模型名。

## Routing Policy

模型路由代码在 `app/backend/services/model_catalog.py`。调用方可以传真实模型名，也可以传稳定别名：

| Alias | Default target | Use case |
| --- | --- | --- |
| `auto-fast` / `auto-cheap` | `APP_AI_CHEAP_MODEL` | 路由、分类、轻量总结、低风险结构化提取 |
| `auto-ocr` | `APP_OCR_MODEL` | 扫描 PDF 页 OCR、图片文字转写 |
| `auto-review` | `APP_AI_REVIEW_MODEL` | 合同审查、案件问答、结构化法律分析 |
| `auto-agentic` | `APP_AI_AGENTIC_MODEL` | Agentic planning, tool orchestration, and low-risk multi-step routing. |
| `auto-grounded-research` | `APP_AI_GROUNDED_RESEARCH_MODEL` | Grounded research, source-backed synthesis, and citation-oriented review. |
| `auto-pdf` | `APP_AI_PDF_MODEL` | 大 PDF、复杂推理、最终复核 |
| `auto-image` | `APP_AI_IMAGE_MODEL` | 图片生成、图片编辑、视觉证据草图 |

显式模型名会原样透传给网关，因此新 Gemini 模型发布后，可以先通过 `.env` 或请求参数接入，不需要立刻改代码。

`/api/v1/aihub/models` 还会返回 `budget_policy`：它解释每个任务为什么使用 cheap-first、balanced 或 premium-exception 策略，并标出显式 premium 模型是否超过该任务预算。默认 `APP_AI_PREMIUM_REQUIRES_REVIEW=true`，用于提示维护者对非 PDF/非媒体场景的 premium 使用做人工确认。

`model_configuration_audit` 检查当前 `.env` 解析出的 cheap、fast、OCR、classification、review、premium 和 PDF 角色是否符合成本层级和能力预期。`APP_AI_FAST_MODEL`、`APP_OCR_MODEL`、`APP_AI_CLASSIFIER_MODEL` 现在会优先用于对应任务，未配置时回退到 cheap model。

`model_ops_readiness` 汇总配置审计、路由、推理预算、请求参数、调用点审计、遥测、守卫、回放、回退链和成本控制，给出模型运维是否可发布的 pass/warn/fail 结论。
`default_optimization` 将能力矩阵和成本预测转成默认模型调优计划，指出哪个 env var 应该回到最便宜的可用 Gemini 模型，以及预计月度节省。
`gateway_compatibility` 识别 `models/`、`google/`、`openrouter/google/` 等网关前缀形式，让本地成本和能力判断仍能映射到 canonical Gemini 模型。
`gateway_health_plan` 检查 `APP_AI_BASE_URL`、`APP_AI_KEY` 是否已安全配置，生成 `/models` 和低价 JSON probe 的占位符请求，并确认高频任务仍使用便宜 Gemini 默认模型；它不会自动调用网关。
`gateway_connection_profile` adds the runtime connection-shape guard before `gateway_health_plan`: a remote bare OpenAI-compatible host such as `https://yibuapi.com` is normalized to `/v1`, credential-bearing URLs are blocked in evidence, and key presence is shown only as `{{APP_AI_KEY}}`.
`gateway_runtime_configuration` adds the runtime setup guard between the connection profile and health plan. It verifies `APP_AI_BASE_URL` normalization, `APP_AI_KEY` placeholder display, cheap-first Gemini role defaults, and safe probe order (`/models` -> cheap JSON -> small fixture smoke) without calling a provider, writing `.env`, changing defaults, shifting traffic, or returning keys, headers, prompts, request/response bodies, raw legal text, model outputs, gateway responses, emails, or user identifiers.
`modelops-newapi-channel-bootstrap` adds the reviewer-facing setup packet for a NewAPI/YibuAPI/OpenAI-compatible channel. It normalizes a bare channel URL to `/v1`, converts supplied key presence into the `APP_AI_KEY` placeholder, joins connection-profile/runtime-configuration/observed-model intake/coverage-gap/premium-exception review evidence, and recommends cheap-first Gemini env defaults before any live request. The packet is visible in both `/model-ops` and `/maintenance` so operations and release reviewers see the same sanitized bootstrap state. It does not call NewAPI, Gemini, OpenAI, Google, yibuapi, gateways, app AI endpoints, models, or the network; write `.env` or defaults; shift traffic; or return raw payloads, prompts, legal text, model outputs, gateway responses, emails, identifiers, or credentials.

`modelops-gemini-official-cheap-first-source-review` is the metadata-only
source and price-ratio review for the cheap-first Gemini text defaults. It
links the official Gemini models and pricing pages as review anchors, compares
local catalog prices for `gemini-2.5-flash-lite`, `gemini-2.5-flash`, and
`gemini-2.5-pro`, and checks that high-frequency cheap, fast, classification,
and OCR routes remain Flash-Lite aligned before default-promotion claims are
allowed. It does not scrape live pricing, call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, models, or the network, write configuration, change
defaults, shift traffic, claim pricing accuracy, claim automatic default
changes, or expose keys, Authorization headers, request bodies, response
bodies, prompts, raw payloads, legal text, model outputs, emails, identifiers,
or credentials.

`model-gateway-probe-runbook-gate` adds the ordered maintainer runbook between gateway health planning and probe evaluation. It requires runtime/channel normalization and secret-boundary review, then list-models evidence, cheap JSON probe evidence, optional image smoke, small synthetic legal fixture smoke, and default-change review in that order. The gate is visible in `/model-ops` and the aggregate ModelOps API, but it does not call NewAPI, Gemini, OpenAI, Google, yibuapi, gateways, app AI endpoints, models, or the network; write configuration; change defaults; shift traffic; or return raw probe payloads, prompts, legal text, model outputs, gateway responses, headers, emails, identifiers, or credentials.
`gateway_probe_evaluation` 接收维护者手动运行 `/v1/models` 和 tiny chat probe 后的脱敏结果，评估网关实际可用 Gemini 模型，并给出 cheap-first `.env` 推荐。
`lifecycle_policy` 检查 Gemini/NewAPI 默认模型是否固定到稳定、具体、低价优先的模型 ID；preview 模型和 `latest` 别名只能作为显式实验，Gemini 1.x、1.5 和 2.0 代停用模型不得作为默认值。

`task_inference` 让 `POST /api/v1/aihub/gentxt` 默认使用 `task=auto`，通过确定性规则把分类、OCR、法律审查、预检/摘要等请求映射到合适任务，避免忘传 `task=review` 时把法律审查误放到 fast 路由。

`callsite_audit` 会静态扫描后端 service 层 `GenTxtRequest` 调用，确保关键业务调用显式写出 `task=...`，避免新增代码只依赖自动推断。

`runtime_router` 将 `task`、`model` 和 `allow_over_budget_model` 转换为实际模型；默认会把超预算或需要人工复核的显式模型降级到任务推荐模型。

Runtime default drift is also guarded: for text and embedding tasks, if the configured task default points at an unknown gateway id, a preview/review lifecycle model, an unpriced catalog row, or a model above the task budget, `model_budget` keeps that configured value visible for operations evidence but `model_runtime_router` sends the request to the catalog-safe stable, priced, within-budget recommendation from `model_default_candidate_selector`. PDF and media defaults remain explicit exception routes.

`reasoning_policy` 为 Gemini/OpenAI-compatible `reasoning_effort` 设置任务默认值：高频 fast/OCR/classification 尽量关闭或最小化 thinking，法律 review 使用 low，PDF/复杂复核才使用 high。未知网关模型会省略该参数以保持透传兼容。

`request_policy` 为 `temperature` 和 `max_tokens` 设置任务级默认值和上限：高频分类、OCR 和预检请求默认短输出、低温度，法律 review/PDF 保留更大的显式输出预算，JSON 输出会降低温度上限以减少解析失败和重试成本。
`request_cost_bounds` 将 `request_policy` 的 token 上限换算成按任务的默认请求成本和上限请求成本，帮助维护者发现 fast、classification、OCR 等高频路径是否被误调到高价模型或过大输出预算。
`cache_policy` 为 fast、classification、OCR、review 和 PDF 定义 hash-only 缓存边界、TTL、命中率假设和预计节省；PDF 文档分析默认禁用缓存。

`route_telemetry` 记录运行时路由聚合指标，包括自动推断比例、降级比例、超预算请求、人工复核请求和未知价格模型，帮助维护者确认 cheap-first 策略是否在真实调用中生效。

`route_guardrails` 将路由遥测转换成 pass/warn/fail 检查，覆盖失败率、超预算比例、降级比例、人工复核比例、未知价格模型和允许超预算次数，帮助维护者在发布前发现 cheap-first 路由漂移。

同一接口还会返回 `capability_matrix`：它按任务列出 required capabilities、max cost tier、runtime default、recommended model 和候选模型数量。矩阵先过滤能力不满足的模型，再按 stable 状态、成本、延迟和 fit score 排序；未知 NewAPI 模型名仍可透传，但不会被视为已验证价格模型。

`escalation_policy` 定义 cheap-first cascade：高频任务先用 cheap model，低置信、JSON/schema 失败、引用/证据/质量门禁失败时才进入 verify 或 retry-up；`privacy_high`、`instruction_high`、`extraction_quality_fail` 这类信号会硬停止，避免把不安全或不可审查输入继续送进更贵模型。

`fallback_chains` 将升级策略和能力矩阵合并成每个任务的 primary / verify / fallback / premium-exception 顺序，帮助维护者在 NewAPI/Gemini 网关模型不可用或质量不足时仍保持低价优先。

`cost_forecast` 基于当前模型目录、升级策略和默认月度任务画像估算 cheap-first cascade 成本，并与 premium-only baseline 对比，帮助维护者量化低价优先策略的节省幅度。

`cost_guardrails` 将模型用量、成本预测和预算阈值合并成 pass/warn/fail 检查，覆盖预算占用、失败率、premium 请求比例、未知价格模型和 cheap-first 节省幅度。

`routing_replay` 使用固定法律工作流场景回放当前升级策略，检查高频任务是否仍从便宜模型开始、警告/失败信号是否按预期验证或升级、premium 例外是否仍需要人工复核、硬停止是否避免继续花费模型预算。

`gateway_request_compatibility_gate` is the shipped metadata-only request-shape
gate for OpenAI-compatible Gemini/NewAPI gateways. It joins task defaults,
gateway model compatibility, request parameter caps, reasoning-effort defaults,
JSON response-format requirements, and cheap-first cost bounds before any live
model call is attempted. The evidence does not call NewAPI, Gemini, OpenAI,
Google, gateways, or the network, does not write configuration or shift traffic,
and does not include headers, request bodies, prompts, raw legal text, model
outputs, payloads, emails, or credentials.

## Cost-First Defaults

当前默认策略：

- 高频、低风险任务使用 `gemini-2.5-flash-lite`：OCR、材料分类、Plan Mode 理解、预检、轻量结构化处理。
- 法律审查主体流程使用 `gemini-2.5-flash`：风险识别、条款映射、法律分析、案件问答。
- 只在必要时使用 `gemini-2.5-pro`：大 PDF、复杂推理、最终复核或低价模型失败后的人工指定升级。
- Gemini 3 系列用于显式能力升级：`gemini-3.1-flash-lite` 适合低成本 agentic/grounding 任务，`gemini-3.5-flash` 已按官方价格刷新为稳定 premium 复核候选，`gemini-3.1-pro-preview` 和 `gemini-3.1-pro-preview-customtools` 只作为预览 premium 复核候选。

这样做的依据是 Gemini 官方价格页将 `gemini-2.5-flash-lite` 描述为面向规模化使用的最小、最具成本效益模型，并给出低于 Flash/Pro 的输入输出价格。官方模型页也标注 `gemini-2.5-flash` 适合低延迟、高吞吐且需要推理的任务，`gemini-2.5-pro` 用于复杂任务和深度推理。

`APP_AI_AGENTIC_MODEL` and `APP_AI_GROUNDED_RESEARCH_MODEL` pin the agentic and grounded-research task defaults to `gemini-3.1-flash-lite`. This is a metadata-only/default routing change: the ModelOps coverage evidence should treat these defaults as ready items, including the previously missing agentic default row, and it must not call NewAPI, Gemini, OpenAI, Google, gateways, or the network, write real environment values, or include raw prompts, payloads, model outputs, or credentials.

`modelops-default-template-alignment` is the shipped metadata-only alignment audit
for this default set. It keeps the Settings defaults in `app/backend/core/config.py`,
`app/backend/.env.example`, the README env block, and this strategy document aligned
for the Gemini cheap-first defaults, including `APP_AI_AGENTIC_MODEL` and
`APP_AI_GROUNDED_RESEARCH_MODEL`. The audit evidence does not call NewAPI, Gemini,
OpenAI, Google, gateways, or the network, does not write real environment values,
and does not include raw prompts, payloads, model outputs, or credentials.

`modelops-gemini-default-change-review` is the shipped metadata-only proposal
review evidence for a future task-default change to a new Gemini variant. Before
maintainers apply such a default, the evidence scope requires checking the
candidate cost tier, lifecycle status, task capabilities, gateway compatibility,
and premium/manual review boundary. It does not call NewAPI, Gemini, OpenAI,
Google, gateways, or the network, does not write real environment values, and
does not include raw prompts, payloads, model outputs, or credentials.

`modelops-gemini-default-cost-impact` is the shipped metadata-only cost impact
forecast evidence for a future task-default change to a new Gemini variant.
Before maintainers apply such a default, the evidence scope requires checking
estimated monthly cost delta, cheap-first savings or regression, unknown
pricing, and the premium exception/manual review boundary. It does not call
NewAPI, Gemini, OpenAI, Google, gateways, or the network, does not write real
environment values, and does not include raw prompts, payloads, model outputs,
or credentials.

`modelops-observed-gemini-model-intake-queue` is the shipped metadata-only
intake queue evidence for OpenAI-compatible gateway `/models` or manually
observed Gemini-like model ids before they enter default candidates. The queue
scope normalizes ids and records known/unknown status, price, lifecycle, cost
tier, cheap-first eligibility, default-promotion block/review/ready state,
promotion safety checks, cheap-first candidate summaries, and maintainer runbook
steps. Unknown Gemini-like ids block default promotion, review-only rows stay
outside default queues, and ready Flash-Lite-style candidates still require
selector replay, catalog impact replay, default-change queue, canary, approval,
rollback, and maintainer checklist evidence before any configuration edit. It
does not call NewAPI, Gemini, OpenAI, Google, gateways, or the network, does not
write real environment values or shift traffic, and does not include raw
prompts, payloads, model outputs, legal text, emails, or credentials.

`modelops-observed-gemini-coverage-gap-queue` is the shipped metadata-only
coverage queue for observed Gemini-like model ids. It joins the observed intake
queue with the Gemini variant matrix, then records Gemini family coverage gaps,
high-frequency cheap-first task gaps, unknown/unpriced/preview/media risk, and
premium or non-cheap default-promotion review actions. It does not call NewAPI,
Gemini, OpenAI, Google, gateways, or the network, write configuration, shift
traffic, or include raw prompts, payloads, model outputs, credentials, or
emails.

`model-catalog-candidate-patch-plan` is the shipped metadata-only catalog
maintenance plan for unknown observed Gemini-like model ids. It creates manual
`ModelProfile` candidate stubs, required source/pricing/lifecycle/capability
checks, cheap-first boundaries, and explicit-only default-promotion states. It
does not edit `model_catalog.py`, write configuration, call a gateway or the
network, shift traffic, or include raw payloads, prompts, legal text, model
outputs, credentials, or emails.

`modelops-legal-micro-benchmark-preflight` is the shipped metadata-only
low-resource run-planning packet for the smallest cheap-first legal benchmark.
It selects synthetic fixture ids, document case ids, fact-consistency case ids,
serial run order, cost estimates, and follow-up gate endpoints before any
maintainer treats a cheap Gemini result as default-promotion evidence. It does
not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, or the
network, write configuration, shift traffic, or include request bodies,
messages, prompts, fixture excerpts, legal text, generated document text, model
outputs, gateway responses, credentials, or emails.

`gemini-newapi-model-alias-matrix` is the shipped metadata-only alias evidence
for gateway-specific Gemini model names. It maps canonical, `models/`,
`google/`, `google:`, `yibu/`, and nested provider aliases back to local catalog
ids, then exposes cheap-first eligibility, premium/manual review boundaries,
unknown-model review states, and sensitive/invalid/total rejection counts. It does not
call NewAPI, Gemini, OpenAI, Google, gateways, or the network, does not write
configuration, and does not include raw prompts, payloads, legal text, model
outputs, credentials, or emails.

`modelops-legal-fixture-cheap-first-benchmark-gate` is the shipped
metadata-only small legal-document cheap-first Gemini benchmark/risk gate
evidence. It uses redacted fixture ids, document case ids, fact-consistency case
ids, local rule baseline case ids and match counts, expected issue counts,
document benchmark pass/fail counts, coverage-gap counts, linked Gemini/NewAPI
cheap-first calibration task ids, calibration decisions, calibration release
gates, cost metadata, and escalation metadata to
decide whether a cheap-first result remains acceptable or needs
review/escalation. It is visible through maintenance evidence, direct AIHub
ModelOps endpoints, the aggregate `/api/v1/aihub/models` payload, and the
ModelOps main page. It does not call NewAPI, Gemini, OpenAI, Google, gateways,
or the network, and it does not include real legal text, fixture snippets,
local rule predictions, extracted field values, candidate generated text,
prompts, calibration payloads, model outputs, credentials, or emails.

`legal-rag-embedding-batch-budget-gate` is the shipped metadata-only
low-resource batch budget gate for Legal RAG embeddings. It consumes the
embedding index dry-run manifest, keeps text embeddings on
`gemini-embedding-001`, uses the local catalog batch price from the Gemini
embedding cheap-first preflight, and exposes planned batch counts, laptop-safe
chunk/token limits, estimated token totals, and release actions before any
embedding run. It does not call NewAPI, Gemini, OpenAI, Google, gateways, app
AI endpoints, models, indexes, databases, or the network, and it does not
claim live pricing accuracy, embedding execution, index writes, or retrieval
quality.

`legal-rag-embedding-batch-approval-packet` is the shipped metadata-only
maintainer review packet downstream of the batch budget gate. It maps budget
rows to serial queue order, `max_parallel_embedding_requests=1`, required
maintainer/RAG-index reviewer roles, pre-approval checks, and advance/hold/block
actions before any cheap Gemini embedding run. It does not approve a batch,
collect approver identity, write approval records, call NewAPI, Gemini, OpenAI,
Google, gateways, app AI endpoints, models, indexes, databases, or the network,
and it does not claim live pricing accuracy, embedding execution, index writes,
or retrieval quality.

`legal-rag-embedding-batch-observation-gate` is the shipped metadata-only
aggregate observation gate downstream of the approval packet. It reviews
sanitized observed batch/chunk/vector-slot/token counts, cost deltas,
`max_parallel_embedding_requests=1`, and allow/hold/block index-review actions
after an external cheap Gemini embedding run. It does not approve maintainers,
execute embeddings, collect approver identity, call NewAPI, Gemini, OpenAI,
Google, gateways, app AI endpoints, models, indexes, databases, or the network,
and it does not return source ids, approval item ids, raw legal text, source
chunks, embedding vectors, prompts, model outputs, gateway payloads,
credentials, emails, live pricing claims, index writes, or retrieval quality.

`legal-rag-embedding-index-commit-review-packet` is the shipped metadata-only
maintainer review packet downstream of aggregate embedding observations. It
turns ready observation rows into commit-review items with vector-slot match
evidence, observed chunk/cost evidence, required maintainer/RAG-index/privacy
signoffs, pre-commit checks, and prepare/hold/block actions before any real
index commit. It does not approve committers, execute embeddings, collect
committer identity, call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, indexes, databases, or the network, and it does not write
indexes or return source ids, approval item ids, raw legal text, source chunks,
embedding vectors, prompts, model outputs, gateway payloads, credentials,
emails, live pricing claims, or retrieval quality.

`legal-rag-embedding-index-post-commit-verification-gate` is the shipped
metadata-only post-commit verification gate downstream of commit review. It
turns sanitized post-commit observations into verification rows with expected
versus observed vector slots, index entry counts, metadata records, retrieval
locators, checksum counts, failed-entry totals, rollback signals, and
allow/hold/block retrieval-diagnostics review actions. It does not approve or
execute index commits, enable production retrieval, call NewAPI, Gemini,
OpenAI, Google, gateways, app AI endpoints, models, indexes, databases, or the
network, and it does not write indexes or return source ids, approval item ids,
raw legal text, source chunks, embedding vectors, prompts, model outputs,
gateway payloads, credentials, emails, live pricing claims, index quality, or
retrieval quality.

`legal-rag-embedding-retrieval-diagnostics-handoff-gate` is the shipped
metadata-only handoff gate between post-commit verification and retrieval
diagnostics review. It converts verified, review, and blocked verification
rows into safe ready/hold/block handoff rows with diagnostics-review-only
actions, rollback review links, safe payload field lists, and production
retrieval false flags. It does not execute retrieval diagnostics, enable
production retrieval, claim index or retrieval quality, call NewAPI, Gemini,
OpenAI, Google, gateways, app AI endpoints, models, indexes, databases, or the
network, and it does not write indexes or return source ids, raw query, user
questions, retrieved context, raw legal text, source chunks, embedding vectors,
prompts, model outputs, gateway payloads, credentials, emails, committer
identity, live pricing claims, legal advice, or client delivery claims.

`legal-rag-answer-release-readiness-gate` is the shipped metadata-only answer
release gate after retrieval observation review. It maps sanitized retrieval
observation rows to ready/review/block answer-release rows, internal draft
actions, citation packet requirements, lawyer-review requirements, cheap-first
verify/escalate boundaries, and client-delivery false flags. It does not call
NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, indexes, or
the network, and it does not write answers, send client delivery, claim legal
advice or answer quality, or return source ids, raw query, user questions,
retrieved context, raw legal text, prompts, model outputs, gateway payloads,
credentials, emails, or client material.

`modelops-legal-fixture-cheap-first-default-promotion-packet` is the shipped
metadata-only maintainer review packet for cheap-first legal fixture default
promotion. It consumes the legal fixture gate, document benchmark metadata,
fact-consistency metadata, local rule baseline metadata, and linked cheap-first
calibration metadata, then exposes only ids, statuses, counts, calibration
decisions/release gates, cost tiers, reason codes, and signoff roles. It never
writes configuration, calls
NewAPI, Gemini, OpenAI, Google,
gateways, or the network, shifts traffic, or claims that a default has been
approved. It does not return local rule predictions or extracted field values.
The ModelOps main page now displays it next to the legal fixture gate
so maintainers can review promotion readiness without opening maintenance-only
evidence pages.

`legal-public-fixture-priority-queue` is the maintenance-side metadata bridge
from public legal benchmark source taxonomies into the next synthetic legal
fixture work. It prioritizes LawBench, LexEval, LegalBench, LegalBench-RAG,
CUAD, LexGLUE, CaseGen, and corpus-scale references by user-need links,
local-baseline status, and document/corpus mapping gaps before maintainers
expand cheap-first legal benchmark evidence. It does not call NewAPI, Gemini,
OpenAI, Google, gateways, app AI endpoints, models, or the network, does not
download public datasets or import public benchmark samples, does not change
default models or routes, and does not return raw legal text, fixture snippets,
small-corpus excerpts, prompts, model outputs, gateway payloads, or credentials.

`user-need-legal-document-benchmark-evidence` is the maintenance-side bridge
that prevents cheap-first legal fixture evidence from being treated as
user-need-ready until document benchmark status, fact-consistency status, local
rule baseline status, and cheap-first gate status are visible together. It does
not call models or gateways, does not change defaults, and does not return raw
legal text, document snippets, fixture snippets, prompts, payload bodies, model
outputs, or credentials.

`feedback-user-need-legal-document-benchmark-backlog` is the feedback-driven
maintenance backlog that maps privacy-safe feedback clusters into user-need and
legal-document benchmark fixture/review actions before any cheap-first default
claim is made. It does not call models or gateways, does not change defaults,
and does not return raw feedback, PII, uploaded document text, prompts, payload
bodies, model outputs, or credentials.

`modelops-gemini-cheap-first-route-preflight` is the shipped metadata-only route
preflight for Gemini cheap-first defaults. It joins official source refresh
notes, local task defaults, the Gemini variant matrix, gateway alias capability
coverage, observed model id metadata from the ModelOps POST review form, and
the cheap-first coverage gate so high-frequency work stays on stable Flash-Lite
routes while preview, premium, media, unknown, unpriced, or retired variants
remain review/explicit-only. It does not call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, or the network, does not write configuration or
shift traffic, and does not include request/response bodies, headers, prompts,
raw payloads, legal text, model outputs, gateway responses, credentials,
emails, or user identifiers.

`modelops-observed-gateway-model-fit-matrix` is the shipped metadata-only bridge
from sanitized OpenAI-compatible gateway `/models` IDs to task policy fit. It
maps observed model IDs to canonical Gemini catalog rows, cheapest observed
task candidates, missing task coverage, and review-only Pro, preview, media,
unknown, external, and unpriced boundaries. It does not call NewAPI, Gemini,
OpenAI, Google, gateways, app AI endpoints, models, or the network, write
configuration, shift traffic, validate live account inventory, or include
request/response bodies, headers, prompts, raw payloads, legal text, model
outputs, gateway responses, credentials, emails, or user identifiers.

`modelops-runtime-explicit-model-fit-gate` is the shipped metadata-only runtime
route review gate for explicit model requests. It runs sanitized task/model
scenarios through the local runtime router, then shows unknown gateway guards,
reviewed gateway pass-through exceptions, explicit over-budget exceptions,
local downgrades to the recommended model, cheap-first alignment, and observed
gateway fit review states.
It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints,
models, or the network, write configuration, change runtime behavior, change
defaults, shift traffic, validate live account inventory, or include request or
response bodies, headers, messages, prompts, raw payloads, legal text, model
outputs, gateway responses, credentials, emails, or user identifiers.

## Current Gemini Coverage

目录中列出并公开给 `/api/aihub/models` 的模型包括：

- `gemini-2.5-flash-lite`
- `gemini-2.5-flash`
- `gemini-2.5-pro`
- `gemini-3.1-flash-lite`
- `gemini-3.5-flash`
- `gemini-3.1-pro`
- `gemini-3.1-pro-preview`
- `gemini-3.1-pro-preview-customtools`
- `gemini-2.5-flash-image`
- `gemini-3.1-flash-image`
- `gemini-3-pro-image`

`model_default_candidate_selector.py` derives cheapest capable Gemini task
recommendations from local catalog metadata instead of relying only on
hard-coded model ids. Runtime defaults remain unchanged, but ModelOps evidence
can promote a future stable, lower-cost Flash-Lite catalog row in review
metadata only when that row is `default_eligible`. The ladder must keep
`default_eligible` candidates separate from `review-only` candidates; preview,
unpriced, premium-over-budget, premium-exception-only, unknown, deprecated, and
media-route variants may be shown for context or manual review but must not be
rendered by UI or maintainers as directly promotable defaults. See
`docs/MODEL_DEFAULT_CANDIDATE_SELECTOR.md`.

`gemini-2.0-flash` 和 `gemini-2.0-flash-lite` 不再作为推荐项，因为 Google 价格页标注它们已经在 2026-06-01 停用。若某个中转网关仍提供兼容别名，仍可通过显式模型名透传，但不应作为默认配置。

## Official Price And Status Gate

If official provider or gateway pricing, lifecycle status, or model availability
has not been confirmed from current source-review evidence, the model must stay
`unpriced` and `review-only`. Do not hard-code a cost, include it in cheap-first
savings claims, or promote it as `default_eligible` until price, status,
capability, gateway evidence, and task budget fit are refreshed.

As of the 2026-06-09 source refresh, `gemini-3.5-flash` is cataloged as a
stable premium review candidate with token pricing, and
`gemini-3-pro-image` is cataloged as a stable premium explicit-media candidate
with image pricing. These updates do not change the high-frequency defaults:
Flash-Lite remains first for cheap, fast, OCR, classification, agentic, and
grounded-research paths unless a separate default-change review passes.

## Operational Notes

- 不要把 `APP_AI_KEY` 写入 README、issue、commit message 或截图。
- 若密钥曾经出现在聊天、日志或远程仓库中，应在网关后台立即轮换。
- 新增模型时优先改 `.env`，确认稳定后再补充 `model_catalog.py` 的公开目录。
- 批量任务上线前先调用 `/api/v1/aihub/models` 确认当前路由角色。
- 维护者可以打开前端 `/model-ops` 或调用 `/api/v1/aihub/models/usage` 查看本进程内模型请求次数、成功/失败计数、平均延迟和 token 汇总。
- `/model-ops` 会展示 Model ops readiness，把分散的模型运维信号汇总成发布前的阻塞和告警结论。
- `/model-ops` 会展示 Default optimization，帮助维护者把 fast、classification、OCR、review 和 PDF 默认模型保持在最便宜的合格 Gemini 路径上。
- `/model-ops` 会展示 Gateway compatibility，帮助维护者确认 NewAPI 或其他 OpenAI-compatible 网关返回的 Gemini 前缀模型名仍能匹配本地目录。
- `/model-ops` 会展示 Gateway health plan，帮助维护者在真实请求前检查 base URL、key 配置状态和低价 probe 请求。
- `/model-ops` 和 `/api/v1/aihub/models/gateway-probe-evaluation` 会评估脱敏后的 `/v1/models` 和 tiny chat probe 结果，辅助选择最便宜的可用默认模型。
- `/model-ops` 会展示 Lifecycle policy，帮助维护者在发布前拒绝 deprecated、preview、latest 或未知网关默认模型。
- `/model-ops` 会展示 Budget policy，帮助定位哪些任务仍在使用 premium 或未知价格模型。
- `/model-ops` 会展示 Configuration audit，帮助维护者确认环境变量解析出的模型角色没有误配成高价或能力不足模型。
- `/model-ops` 会展示 Runtime router 和 auto task inference，帮助维护者确认 `gentxt` 请求字段、任务默认模型和自动推断规则。
- `/model-ops` 会展示 Reasoning policy，帮助维护者确认 thinking budget 是否仍按任务低价优先。
- `/model-ops` 会展示 Request policy，帮助维护者确认 temperature 和 max_tokens 是否仍按高频任务低成本策略执行。
- `/model-ops` 会展示 Request cost bounds，帮助维护者把 max_tokens 策略映射成默认请求成本和上限请求成本。
- `/model-ops` 会展示 Cache policy，帮助维护者确认重复请求只能使用哈希元数据缓存，并估算节省。
- `/model-ops` 会展示 Route telemetry，帮助维护者观察真实请求的自动推断、降级和超预算情况。
- `/model-ops` 会展示 Route guardrails，帮助维护者把运行时路由遥测转成发布前的阻塞和告警项。
- `/model-ops` 会展示 Callsite audit，帮助维护者确认 service 层 AIHub 文本调用都带有显式 task。
- `/model-ops` 会展示 Escalation policy，帮助维护者确认哪些质量信号会触发平衡模型验证或 premium exception。
- `/model-ops` 会展示 Fallback chains，帮助维护者确认每个任务的低价主模型、回退模型和 premium 人工复核边界。
- `/model-ops` 会展示 Routing replay，帮助维护者在发布前发现 cheap-first 路由漂移。
- `/model-ops` 会展示 Cost forecast，帮助维护者确认高频任务是否仍然保留足够的 cheap-first 成本优势。
- `/model-ops` 会展示 Cost guardrails，帮助维护者尽早发现 premium 使用、失败重试或未知价格模型导致的成本漂移。
- 模型用量统计只保存聚合指标，不保存 prompt、用户文档、文件名、邮箱、API key 或其他敏感内容。
- `/model-ops` 中的 estimated cost 使用 `model_catalog.py` 里的 Gemini paid-tier token 单价估算，仅用于成本趋势判断；实际扣费以 NewAPI/Google Gemini 账单为准。

## Route Telemetry Triage

`route_telemetry_triage` is the actionable cheap-first review layer for
persisted route telemetry. It consumes `route_telemetry_ops_summary` checks and
daily rows only, then prioritizes failures, premium-model drift, over-budget
pressure, operator-review load, unknown gateway models, daily hotspots, and
missing staging telemetry. It does not read prompts, legal text, gateway
payloads, credentials, emails, or raw model output.

`route_telemetry_remediation` turns that triage queue into reviewed repair
steps and optional `.env` suggestions. It never writes configuration and never
calls NewAPI, Gemini, OpenAI, or another gateway; maintainers must apply changes
manually and rerun the listed validation commands.

`default_change_queue` turns default-optimization recommendations into
maintainer queue items. It marks each env-var change as ready,
review-required, blocked, or no-action based on the cheap-first release
decision, gateway probe status, catalog source audit, and price refresh monitor.
It never writes configuration automatically.

`cheap_first_canary_plan` consumes the default-change queue downstream. It turns
ready changes into 1%, 10%, and 25% canary review steps with holdouts, rollback
triggers, and observation windows, while keeping review-required or blocked
changes at 0% traffic. It is metadata-only and does not write configuration,
call a gateway, or claim that production traffic shifted.

`cheap_first_canary_observation` consumes sanitized aggregate observation counts
for those steps. It checks failure, over-budget, premium/unknown-price, and
operator-review ratios against rollout thresholds, rejects sensitive field names
without echoing values, and never persists observations or advances traffic.

`cheap_first_canary_promotion_decision` consumes the canary plan and observation
review. It returns advance-next-batch, hold-for-review, rollback-required,
monitor-only, or not-ready decisions for maintainers, while keeping
configuration writes, gateway calls, and traffic shifts disabled.

`cheap_first_canary_approval_packet` converts those promotion decisions into
maintainer signoff requirements and pre-approval checks. It does not record
approval identity, approve automatic rollout, write configuration, call a
gateway, or shift traffic.

`cheap_first_canary_rollback_drill` consumes the approval packet downstream and
returns rollback rehearsal tasks, trigger-review status, holdout confirmation
requirements, and role labels. It is metadata-only: it does not execute
rollback, persist drill state, write configuration, call a gateway, or shift
traffic.

## Price Refresh Monitor Integration

`price_refresh_monitor` is included in `GET /api/v1/aihub/models` and in
`model_ops_readiness`. It checks high-frequency defaults, local cost forecast
model references, observed gateway model ids, and preview/premium catalog
watchlist entries before a maintainer treats a Gemini/NewAPI model as a default.

The `/model-ops` page displays this monitor beside cheap-first calibration and
lifecycle policy. Unknown Gemini-like gateway ids, premium or preview observed
models, missing price metadata, and reviewed pass-through exceptions stay
visible as drift signals. The monitor is local metadata only: it does not call
NewAPI/Gemini and does not return API
keys, prompts, legal text, client data, or raw model output.

The monitor also checks the image default as media pricing metadata. `APP_AI_IMAGE_MODEL`
must stay on a known, stable, per-image-priced Gemini image model before image
usage is scaled beyond explicit local testing.

`model-catalog-source-audit` now also exposes official source review freshness
for the Gemini pricing and model-list pages. Each source record includes the
last reviewed date, max allowed review age, current/stale status, review scope,
and whether default model promotion is allowed from that source state. If source
review freshness is stale, default-promotion source blocks must be cleared by
refreshing the official Gemini pricing/model review before changing cheap-first
defaults. This remains metadata-only: it does not call Google, Gemini, NewAPI,
OpenAI, gateways, or the network, and it does not include prompts, payloads,
legal text, model outputs, credentials, or real environment values.

`modelops-gemini-official-model-family-roadmap-evidence` maps official Gemini
family coverage into local catalog rows, roadmap gaps, and cheap-first evidence.
Gemini 2.5 text/vision remains the covered stable Flash-Lite default path,
Gemini 3 and image families remain review or explicit-route evidence, and
Live/audio, embedding, and TTS stay gap-queued until catalog, pricing, request
policy, and route boundaries exist. This also remains metadata-only: no
provider, gateway, app AI, model, or network calls are made, and no defaults are
changed automatically.

## PDF and Image Route Evidence

`POST /api/v1/aihub/analyzepdf` and `POST /api/v1/aihub/genimg` now use the same
runtime route telemetry path as text generation. This keeps expensive PDF and
image exception paths visible to model ops without storing prompts, PDF bytes,
uploaded images, generated output URLs, revised prompts, file names, API keys,
client data, or raw model output.

`APP_AI_IMAGE_MODEL` pins the image task default separately from text defaults.
`model=auto` on `POST /api/v1/aihub/genimg` now resolves through `task=image` to
the configured Gemini image model instead of falling back to a balanced text
model. Use `auto-image` when a caller wants an explicit stable alias for the
same route.

## Sources

- Google Gemini OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai
- Google Gemini model list: https://ai.google.dev/gemini-api/docs/models
- Google Gemini pricing and deprecation notes: https://ai.google.dev/gemini-api/docs/pricing
- New API user guide: https://docs.newapi.pro/zh/docs/guide/feature-guide/user/api
## AIHub Endpoint Route Coverage Gate

`modelops-aihub-endpoint-route-coverage-gate` is the shipped metadata-only
AIHub endpoint coverage gate. It inventories text, streaming text, PDF, image,
video, audio, and transcription endpoints for runtime-router coverage,
budget-decision coverage, route telemetry coverage, response route payloads,
task inference response coverage, media usage-unit coverage, and media/speech
catalog review gaps.

The current gate keeps endpoint-level state visible in
`GET /api/v1/aihub/models`: text, streaming text, PDF, image, video, audio,
and transcription routes are runtime-routed and telemetry-backed. Non-streaming
text, streaming text, PDF, image, video, audio, and transcription responses
expose sanitized route/task/budget metadata where the response shape allows it.
Streaming text sends the metadata as the first SSE event with empty content so
legacy content concatenation remains compatible. Image, video, audio, and
transcription responses also expose sanitized usage units so cheap-first cost
review can reason about generated images, generated seconds, input characters,
and audio counts without storing raw payloads. Video, audio, and transcription
defaults remain review-only catalog items until pricing, lifecycle, and gateway
behavior are documented.

This gate does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, or the network, and it does not claim that media/speech
defaults are price-benchmarked.

## AIHub Media/Speech Default Catalog Gate

`modelops-aihub-media-speech-default-catalog-gate` is the required
metadata-only release gate for AIHub media and speech default review. It is
available at
`/api/v1/aihub/models/aihub-media-speech-default-catalog-gate` and in the
aggregate `/api/v1/aihub/models` payload as
`aihub_media_speech_default_catalog_gate`.

The gate reviews image, video, audio, transcription, future Live audio, and
embedding default coverage against local catalog status, explicit media/speech
budget modes, endpoint route coverage, official Gemini/Veo/TTS source anchors,
default release actions, and review items. Non-catalog and future-route defaults
remain explicit-review only until pricing, lifecycle, gateway behavior, and
route policy evidence is attached.

`gemini-media-speech-review-catalog` extends the local review catalog with
source-anchored Gemini/Veo media ids while preserving the current production
defaults. The recognized review-only candidates include
`veo-3.1-lite-generate-preview`, `veo-3.1-fast-generate-preview`,
`veo-3.1-generate-preview`, `gemini-2.5-flash-preview-tts`,
`gemini-3.1-flash-tts-preview`, `gemini-2.5-pro-preview-tts`,
`gemini-3.1-flash-live-preview`, and
`gemini-2.5-flash-native-audio-preview-12-2025`. These models can now be
canonicalized, shown in the official family roadmap, and classified by the
variant matrix as explicit media/speech review candidates, but they do not
replace `APP_AI_VIDEO_MODEL`, `APP_AI_AUDIO_MODEL`, or
`APP_AI_TRANSCRIPTION_MODEL`. Audio and video candidate pricing remains
explicit-review only until per-second, voice, duration, gateway route-shape, and
safety budget controls are implemented.

This gate does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, or the network. It does not write configuration, change
defaults, shift traffic, or include request/response bodies, headers, prompts,
raw payloads, audio, transcripts, legal text, model outputs, gateway responses,
credentials, emails, or user identifiers.

## AIHub Media Runtime Compatibility Gate

`modelops-aihub-media-runtime-compatibility-gate` is required metadata-only
release evidence for AIHub media runtime endpoint shapes. It is available at
`/api/v1/aihub/models/aihub-media-runtime-compatibility-gate` and in the
aggregate `/api/v1/aihub/models` payload as
`aihub_media_runtime_compatibility_gate`.

The gate separates current OpenAI-compatible runtime methods from native
Gemini/Veo/TTS/Live requirements: `genvideo` uses `client.videos.create` and
`client.videos.retrieve`, `genaudio` uses `client.audio.speech.create`,
`transcribe` uses `client.audio.transcriptions.create`, and Live audio has no
AIHub session route yet. Veo, Gemini TTS, Gemini audio-understanding, and Live
audio promotion remain review-only until gateway shape, native adapter,
polling, session, and output-extraction evidence is attached.

This gate does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, or the network. It does not write configuration, change
defaults, shift traffic, or include request/response bodies, headers, prompts,
raw payloads, audio, transcripts, legal text, model outputs, gateway responses,
credentials, emails, or user identifiers.

## Gemini Embedding Cheap-First Preflight

`modelops-gemini-embedding-cheap-first-preflight` is the required
metadata-only release gate for embedding default review. It pins the text
embedding default to `APP_AI_EMBEDDING_MODEL=gemini-embedding-001`, exposes
`auto-embedding` alias coverage, and keeps local catalog pricing and the
cheap-first embedding budget policy visible at
`/api/v1/aihub/models/gemini-embedding-cheap-first-preflight`.

`gemini-embedding-001` is the cheap-first text embedding path. Multimodal
`gemini-embedding-2` remains review-required before any image, audio, video,
PDF, or source-index route can use it. The preflight does not call NewAPI,
Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the network. It
does not write configuration, change defaults, write indexes, shift traffic, or
include source text, raw legal text, source chunks, embedding vectors,
request/response bodies, headers, prompts, raw payloads, model outputs, gateway
responses, credentials, emails, or user identifiers.

`POST /api/v1/aihub/embeddings` is the runtime bridge for cheap-first Legal
RAG embedding execution. It resolves `APP_AI_EMBEDDING_MODEL` through the
runtime router, defaults to `gemini-embedding-001`, calls the
OpenAI-compatible `embeddings.create` method, records sanitized usage and route
telemetry, and returns numeric vectors plus route metadata without echoing input
source text or persisting embedding vectors in telemetry. This enables small
maintainer-run Legal RAG embedding batches while keeping multimodal embedding
and index writes behind separate review gates.

`POST /api/v1/legal-rag/embedding-batch-preview` is the Legal RAG maintainer
smoke-test layer on top of that runtime. It accepts up to five small chunks,
calls `AIHubService.embed_text`, and returns only hashes, vector dimensions,
norms, vector checksums, usage units, route metadata, and budget metadata. It
does not write indexes or databases, return source text/source ids/embedding
vectors, or echo prompts, gateway payloads, model outputs, or credentials.

## Default Recommendation Readiness Binding

`model-ops-default-recommendation-readiness-binding` promotes
`default_recommendation_snapshot` into the required ModelOps readiness table.
The snapshot now emits role-level blocking and warning ids, so cheap-first
default review can see premium, preview, unknown, over-budget, or observed
Gemini catalog-review issues before maintainers edit environment defaults.
This remains metadata-only: it does not call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, or the network, write configuration, shift
traffic, or expose prompts, raw payloads, legal text, model outputs,
credentials, emails, or user identifiers.

## Gentxt Routing Guard

`modelops-gentxt-routing-guard` is the shipped metadata-only boundary evidence
for the text endpoint. It verifies that media and speech routing labels are
rejected for `POST /api/v1/aihub/gentxt` and routed to the review text budget
instead of `APP_AI_VIDEO_MODEL`, `APP_AI_AUDIO_MODEL`, or
`APP_AI_TRANSCRIPTION_MODEL`. The media aliases remain visible through
`GET /api/v1/aihub/models` for media endpoint review, but gentxt does not use
them as text defaults.

The guard is deterministic and local-only. It does not call NewAPI, Gemini,
OpenAI, Google, gateways, app AI endpoints, models, or the network, and it does
not return prompts, request bodies, response bodies, raw payloads, legal text,
model outputs, gateway responses, credentials, emails, or user identifiers.
## Route Telemetry Result Archive

`route_telemetry_result_archive` is the reviewable archive layer for sanitized
route telemetry. It joins the local route telemetry repository, operations
summary, triage queue, and remediation plan into daily archive rows, task/model
cost ledger rows, and release-review rows that maintainers can inspect before
changing cheap-first defaults.

The archive is metadata-only. It does not call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, models, or the network. It does not write
configuration, change default routes, shift traffic, claim production health, or
claim public benchmark scores. Unknown or unpriced gateway models stay
review-only and unpriced until source-backed catalog and pricing evidence is
refreshed.
