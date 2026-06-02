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

## Cost-First Defaults

当前默认策略：

- 高频、低风险任务使用 `gemini-2.5-flash-lite`：OCR、材料分类、Plan Mode 理解、预检、轻量结构化处理。
- 法律审查主体流程使用 `gemini-2.5-flash`：风险识别、条款映射、法律分析、案件问答。
- 只在必要时使用 `gemini-2.5-pro`：大 PDF、复杂推理、最终复核或低价模型失败后的人工指定升级。

这样做的依据是 Gemini 官方价格页将 `gemini-2.5-flash-lite` 描述为面向规模化使用的最小、最具成本效益模型，并给出低于 Flash/Pro 的输入输出价格。官方模型页也标注 `gemini-2.5-flash` 适合低延迟、高吞吐且需要推理的任务，`gemini-2.5-pro` 用于复杂任务和深度推理。

## Current Gemini Coverage

目录中列出并公开给 `/api/aihub/models` 的模型包括：

- `gemini-2.5-flash-lite`
- `gemini-2.5-flash`
- `gemini-2.5-pro`
- `gemini-3.1-flash-lite`
- `gemini-3.5-flash`
- `gemini-2.5-flash-image`
- `gemini-3-pro-image`

`gemini-2.0-flash` 和 `gemini-2.0-flash-lite` 不再作为推荐项，因为 Google 价格页标注它们已经在 2026-06-01 停用。若某个中转网关仍提供兼容别名，仍可通过显式模型名透传，但不应作为默认配置。

## Operational Notes

- 不要把 `APP_AI_KEY` 写入 README、issue、commit message 或截图。
- 若密钥曾经出现在聊天、日志或远程仓库中，应在网关后台立即轮换。
- 新增模型时优先改 `.env`，确认稳定后再补充 `model_catalog.py` 的公开目录。
- 批量任务上线前先调用 `/api/aihub/models` 确认当前路由角色。

## Sources

- Google Gemini OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai
- Google Gemini model list: https://ai.google.dev/gemini-api/docs/models
- Google Gemini pricing and deprecation notes: https://ai.google.dev/gemini-api/docs/pricing
- New API user guide: https://docs.newapi.pro/zh/docs/guide/feature-guide/user/api
