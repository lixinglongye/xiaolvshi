# 律审雷达

法律文书智能审查与生成平台。当前项目由 FastAPI 后端、React/Vite 前端、本地法律知识库和文档审查算法模块组成。

## 快速入口

- 项目结构说明：[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
- 后端入口：`app/backend/main.py`
- 前端入口：`app/frontend/src/App.tsx`
- 合同审查知识库：`app/backend/data/legal_knowledge/contract_law_seed.json`
- 后端环境变量示例：`app/backend/.env.example`
- AI 模型路由策略：[docs/AI_MODEL_STRATEGY.md](docs/AI_MODEL_STRATEGY.md)
- 模型配置审计：[docs/MODEL_CONFIGURATION_AUDIT.md](docs/MODEL_CONFIGURATION_AUDIT.md)
- 模型运维就绪汇总：[docs/MODEL_OPS_READINESS.md](docs/MODEL_OPS_READINESS.md)
- 默认模型优化计划：[docs/MODEL_DEFAULT_OPTIMIZATION.md](docs/MODEL_DEFAULT_OPTIMIZATION.md)
- 网关模型兼容性：[docs/MODEL_GATEWAY_COMPATIBILITY.md](docs/MODEL_GATEWAY_COMPATIBILITY.md)
- 网关健康检查计划：[docs/MODEL_GATEWAY_HEALTH_PLAN.md](docs/MODEL_GATEWAY_HEALTH_PLAN.md)
- 网关探测结果评估：[docs/MODEL_GATEWAY_PROBE_EVALUATION.md](docs/MODEL_GATEWAY_PROBE_EVALUATION.md)
- Gemini 模型生命周期策略：[docs/MODEL_LIFECYCLE_POLICY.md](docs/MODEL_LIFECYCLE_POLICY.md)
- 模型能力成本矩阵：`app/backend/services/model_capability_matrix.py`
- 模型任务推断：[docs/MODEL_TASK_INFERENCE.md](docs/MODEL_TASK_INFERENCE.md)
- 模型调用点审计：[docs/MODEL_CALLSITE_AUDIT.md](docs/MODEL_CALLSITE_AUDIT.md)
- 运行时模型路由：[docs/MODEL_RUNTIME_ROUTER.md](docs/MODEL_RUNTIME_ROUTER.md)
- 模型推理预算策略：[docs/MODEL_REASONING_POLICY.md](docs/MODEL_REASONING_POLICY.md)
- 模型请求参数策略：[docs/MODEL_REQUEST_POLICY.md](docs/MODEL_REQUEST_POLICY.md)
- 模型请求成本边界：[docs/MODEL_REQUEST_COST_BOUNDS.md](docs/MODEL_REQUEST_COST_BOUNDS.md)
- 模型缓存策略：[docs/MODEL_CACHE_POLICY.md](docs/MODEL_CACHE_POLICY.md)
- 模型路由遥测：[docs/MODEL_ROUTE_TELEMETRY.md](docs/MODEL_ROUTE_TELEMETRY.md)
- 模型路由守卫：[docs/MODEL_ROUTE_GUARDRAILS.md](docs/MODEL_ROUTE_GUARDRAILS.md)
- 模型升级策略：[docs/MODEL_ESCALATION_POLICY.md](docs/MODEL_ESCALATION_POLICY.md)
- 模型成本预测：[docs/MODEL_COST_FORECAST.md](docs/MODEL_COST_FORECAST.md)
- 模型成本守卫：[docs/MODEL_COST_GUARDRAILS.md](docs/MODEL_COST_GUARDRAILS.md)
- 模型路由回放：[docs/MODEL_ROUTING_REPLAY.md](docs/MODEL_ROUTING_REPLAY.md)
- 模型回退链：[docs/MODEL_FALLBACK_CHAINS.md](docs/MODEL_FALLBACK_CHAINS.md)
- 用户研究与维护说明：[docs/USER_RESEARCH_AND_MAINTENANCE.md](docs/USER_RESEARCH_AND_MAINTENANCE.md)
- 开源维护证明接口：[docs/OSS_MAINTENANCE_EVIDENCE.md](docs/OSS_MAINTENANCE_EVIDENCE.md)
- 用户反馈分类处理：[docs/FEEDBACK_TRIAGE.md](docs/FEEDBACK_TRIAGE.md)
- 反馈路线图映射：[docs/FEEDBACK_ROADMAP_ALIGNMENT.md](docs/FEEDBACK_ROADMAP_ALIGNMENT.md)
- 用户需求雷达：[docs/USER_NEEDS_RADAR.md](docs/USER_NEEDS_RADAR.md)
- 发布就绪清单：[docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md)
- 法律知识库审计：[docs/LEGAL_KNOWLEDGE_AUDIT.md](docs/LEGAL_KNOWLEDGE_AUDIT.md)
- 法律 RAG 评估策略：[docs/LEGAL_RAG_EVALUATION.md](docs/LEGAL_RAG_EVALUATION.md)
- 法律 grounding 快速审计：[docs/LEGAL_GROUNDING_QUICK_AUDIT.md](docs/LEGAL_GROUNDING_QUICK_AUDIT.md)
- 法律审查基准评估：[docs/LEGAL_REVIEW_BENCHMARK.md](docs/LEGAL_REVIEW_BENCHMARK.md)
- 法律审查小型测试文书：[docs/LEGAL_BENCHMARK_FIXTURES.md](docs/LEGAL_BENCHMARK_FIXTURES.md)
- 公开法律 benchmark 轻量采样器：[docs/LEGAL_PUBLIC_BENCHMARK_SAMPLER.md](docs/LEGAL_PUBLIC_BENCHMARK_SAMPLER.md)
- 法律小型测试快速套件：[docs/LEGAL_FIXTURE_QUICK_SUITE.md](docs/LEGAL_FIXTURE_QUICK_SUITE.md)
- 法律小型测试模型矩阵：[docs/LEGAL_FIXTURE_MODEL_MATRIX.md](docs/LEGAL_FIXTURE_MODEL_MATRIX.md)
- 法律小型测试 Prompt 包：[docs/LEGAL_FIXTURE_PROMPT_PACK.md](docs/LEGAL_FIXTURE_PROMPT_PACK.md)
- 法律小型测试网关请求清单：[docs/LEGAL_FIXTURE_GATEWAY_MANIFEST.md](docs/LEGAL_FIXTURE_GATEWAY_MANIFEST.md)
- 法律小型测试运行计划：[docs/LEGAL_FIXTURE_RUN_PLAN.md](docs/LEGAL_FIXTURE_RUN_PLAN.md)
- 法律小型测试运行报告：[docs/LEGAL_FIXTURE_RUN_REPORT.md](docs/LEGAL_FIXTURE_RUN_REPORT.md)
- 法律小型测试证据包：[docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md](docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md)
- 法律小型测试改进计划：[docs/LEGAL_FIXTURE_IMPROVEMENT.md](docs/LEGAL_FIXTURE_IMPROVEMENT.md)
- 深度审查规则预检：[docs/DOCUMENT_PREFLIGHT.md](docs/DOCUMENT_PREFLIGHT.md)
- 文档解析质量审计：[docs/EXTRACTION_QUALITY_AUDIT.md](docs/EXTRACTION_QUALITY_AUDIT.md)
- 隐私识别与脱敏：[docs/PRIVACY_REDACTION.md](docs/PRIVACY_REDACTION.md)
- 文档内提示注入审计：[docs/INSTRUCTION_INJECTION_AUDIT.md](docs/INSTRUCTION_INJECTION_AUDIT.md)
- 深度审查质量门禁：[docs/DEEP_REVIEW_QUALITY_GATES.md](docs/DEEP_REVIEW_QUALITY_GATES.md)
- 深度审查引用审计：[docs/DEEP_REVIEW_CITATION_AUDIT.md](docs/DEEP_REVIEW_CITATION_AUDIT.md)
- 深度审查证据审计：[docs/DEEP_REVIEW_EVIDENCE_AUDIT.md](docs/DEEP_REVIEW_EVIDENCE_AUDIT.md)
- 深度审查交付决策：[docs/DEEP_REVIEW_RELEASE_DECISION.md](docs/DEEP_REVIEW_RELEASE_DECISION.md)
- 深度审查风险评分：[docs/DEEP_REVIEW_RISK_SCORING.md](docs/DEEP_REVIEW_RISK_SCORING.md)

## 本地运行

后端：

```powershell
cd D:\小律师\app\backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

前端：

```powershell
cd D:\小律师\app\frontend
corepack pnpm run dev --host 0.0.0.0 --port 3000
```

法律知识库入库：

```powershell
cd D:\小律师\app\backend
.\.venv\Scripts\python.exe scripts\update_legal_knowledge.py
```

本地未配置 `OSS_SERVICE_URL` / `OSS_API_KEY` 时，上传文件会自动落到 `app/backend/local_storage/`，用于本地测试。

## API Key 配置

后端模型网关配置在 `app/backend/.env`：

```env
APP_AI_BASE_URL=https://your-ai-gateway.example.com/v1
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
```

`app/backend/.env.example` 保留模板，不放真实密钥。
更多模型选择、OpenAI-compatible 网关说明和成本策略见 `docs/AI_MODEL_STRATEGY.md`。
