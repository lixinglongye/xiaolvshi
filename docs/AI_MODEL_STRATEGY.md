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
APP_AI_REVIEW_MODEL=gemini-2.5-flash
APP_AI_PDF_MODEL=gemini-2.5-pro
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
| `auto-pdf` | `APP_AI_PDF_MODEL` | 大 PDF、复杂推理、最终复核 |

显式模型名会原样透传给网关，因此新 Gemini 模型发布后，可以先通过 `.env` 或请求参数接入，不需要立刻改代码。

`/api/v1/aihub/models` 还会返回 `budget_policy`：它解释每个任务为什么使用 cheap-first、balanced 或 premium-exception 策略，并标出显式 premium 模型是否超过该任务预算。默认 `APP_AI_PREMIUM_REQUIRES_REVIEW=true`，用于提示维护者对非 PDF/非媒体场景的 premium 使用做人工确认。

`task_inference` 让 `POST /api/v1/aihub/gentxt` 默认使用 `task=auto`，通过确定性规则把分类、OCR、法律审查、预检/摘要等请求映射到合适任务，避免忘传 `task=review` 时把法律审查误放到 fast 路由。

`callsite_audit` 会静态扫描后端 service 层 `GenTxtRequest` 调用，确保关键业务调用显式写出 `task=...`，避免新增代码只依赖自动推断。

`runtime_router` 将 `task`、`model` 和 `allow_over_budget_model` 转换为实际模型；默认会把超预算或需要人工复核的显式模型降级到任务推荐模型。

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
- `/model-ops` 会展示 Budget policy，帮助定位哪些任务仍在使用 premium 或未知价格模型。
- `/model-ops` 会展示 Runtime router 和 auto task inference，帮助维护者确认 `gentxt` 请求字段、任务默认模型和自动推断规则。
- `/model-ops` 会展示 Callsite audit，帮助维护者确认 service 层 AIHub 文本调用都带有显式 task。
- `/model-ops` 会展示 Escalation policy，帮助维护者确认哪些质量信号会触发平衡模型验证或 premium exception。
- `/model-ops` 会展示 Fallback chains，帮助维护者确认每个任务的低价主模型、回退模型和 premium 人工复核边界。
- `/model-ops` 会展示 Routing replay，帮助维护者在发布前发现 cheap-first 路由漂移。
- `/model-ops` 会展示 Cost forecast，帮助维护者确认高频任务是否仍然保留足够的 cheap-first 成本优势。
- `/model-ops` 会展示 Cost guardrails，帮助维护者尽早发现 premium 使用、失败重试或未知价格模型导致的成本漂移。
- 模型用量统计只保存聚合指标，不保存 prompt、用户文档、文件名、邮箱、API key 或其他敏感内容。
- `/model-ops` 中的 estimated cost 使用 `model_catalog.py` 里的 Gemini paid-tier token 单价估算，仅用于成本趋势判断；实际扣费以 NewAPI/Google Gemini 账单为准。

## Sources

- Google Gemini OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai
- Google Gemini model list: https://ai.google.dev/gemini-api/docs/models
- Google Gemini pricing and deprecation notes: https://ai.google.dev/gemini-api/docs/pricing
- New API user guide: https://docs.newapi.pro/zh/docs/guide/feature-guide/user/api
