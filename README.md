# 律审雷达

法律文书智能审查与生成平台。当前项目由 FastAPI 后端、React/Vite 前端、本地法律知识库和文档审查算法模块组成。

## 快速入口

- 项目结构说明：[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
- 后端入口：`app/backend/main.py`
- 前端入口：`app/frontend/src/App.tsx`
- 合同审查知识库：`app/backend/data/legal_knowledge/contract_law_seed.json`
- 后端环境变量示例：`app/backend/.env.example`
- AI 模型路由策略：[docs/AI_MODEL_STRATEGY.md](docs/AI_MODEL_STRATEGY.md)
- 模型能力成本矩阵：`app/backend/services/model_capability_matrix.py`
- 模型升级策略：[docs/MODEL_ESCALATION_POLICY.md](docs/MODEL_ESCALATION_POLICY.md)
- 用户研究与维护说明：[docs/USER_RESEARCH_AND_MAINTENANCE.md](docs/USER_RESEARCH_AND_MAINTENANCE.md)
- 开源维护证明接口：[docs/OSS_MAINTENANCE_EVIDENCE.md](docs/OSS_MAINTENANCE_EVIDENCE.md)
- 用户反馈分类处理：[docs/FEEDBACK_TRIAGE.md](docs/FEEDBACK_TRIAGE.md)
- 用户需求雷达：[docs/USER_NEEDS_RADAR.md](docs/USER_NEEDS_RADAR.md)
- 发布就绪清单：[docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md)
- 法律知识库审计：[docs/LEGAL_KNOWLEDGE_AUDIT.md](docs/LEGAL_KNOWLEDGE_AUDIT.md)
- 法律 RAG 评估策略：[docs/LEGAL_RAG_EVALUATION.md](docs/LEGAL_RAG_EVALUATION.md)
- 法律审查基准评估：[docs/LEGAL_REVIEW_BENCHMARK.md](docs/LEGAL_REVIEW_BENCHMARK.md)
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
APP_AI_REVIEW_MODEL=gemini-2.5-flash
APP_AI_PDF_MODEL=gemini-2.5-pro
```

`app/backend/.env.example` 保留模板，不放真实密钥。
更多模型选择、OpenAI-compatible 网关说明和成本策略见 `docs/AI_MODEL_STRATEGY.md`。
