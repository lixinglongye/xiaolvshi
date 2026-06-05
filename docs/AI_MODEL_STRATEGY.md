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
`gateway_probe_evaluation` 接收维护者手动运行 `/v1/models` 和 tiny chat probe 后的脱敏结果，评估网关实际可用 Gemini 模型，并给出 cheap-first `.env` 推荐。
`lifecycle_policy` 检查 Gemini/NewAPI 默认模型是否固定到稳定、具体、低价优先的模型 ID；preview 模型和 `latest` 别名只能作为显式实验，Gemini 1.x、1.5 和 2.0 代停用模型不得作为默认值。

`task_inference` 让 `POST /api/v1/aihub/gentxt` 默认使用 `task=auto`，通过确定性规则把分类、OCR、法律审查、预检/摘要等请求映射到合适任务，避免忘传 `task=review` 时把法律审查误放到 fast 路由。

`callsite_audit` 会静态扫描后端 service 层 `GenTxtRequest` 调用，确保关键业务调用显式写出 `task=...`，避免新增代码只依赖自动推断。

`runtime_router` 将 `task`、`model` 和 `allow_over_budget_model` 转换为实际模型；默认会把超预算或需要人工复核的显式模型降级到任务推荐模型。

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

## Cost-First Defaults

当前默认策略：

- 高频、低风险任务使用 `gemini-2.5-flash-lite`：OCR、材料分类、Plan Mode 理解、预检、轻量结构化处理。
- 法律审查主体流程使用 `gemini-2.5-flash`：风险识别、条款映射、法律分析、案件问答。
- 只在必要时使用 `gemini-2.5-pro`：大 PDF、复杂推理、最终复核或低价模型失败后的人工指定升级。
- Gemini 3 系列用于显式能力升级：`gemini-3.1-flash-lite` 适合低成本 agentic/grounding 任务，`gemini-3.5-flash` 适合更强的 grounded research，`gemini-3.1-pro-preview` 只作为预览 premium 复核候选。

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

## Current Gemini Coverage

目录中列出并公开给 `/api/aihub/models` 的模型包括：

- `gemini-2.5-flash-lite`
- `gemini-2.5-flash`
- `gemini-2.5-pro`
- `gemini-3.1-flash-lite`
- `gemini-3.5-flash`
- `gemini-3.1-pro-preview`
- `gemini-2.5-flash-image`
- `gemini-3-pro-image`

`gemini-2.0-flash` 和 `gemini-2.0-flash-lite` 不再作为推荐项，因为 Google 价格页标注它们已经在 2026-06-01 停用。若某个中转网关仍提供兼容别名，仍可通过显式模型名透传，但不应作为默认配置。

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
models, and missing price metadata stay visible as drift signals. The monitor is
local metadata only: it does not call NewAPI/Gemini and does not return API
keys, prompts, legal text, client data, or raw model output.

The monitor also checks the image default as media pricing metadata. `APP_AI_IMAGE_MODEL`
must stay on a known, stable, per-image-priced Gemini image model before image
usage is scaled beyond explicit local testing.

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
