# User Research and Maintenance Notes

本项目面向中国大陆法律文书审查、案件材料整理和诉讼/仲裁准备场景。维护重点不是单次生成演示，而是把律师、企业法务和个人用户的高频工作流做成可复核、可追踪、可降本的系统。

## Primary Users

| User | Main job | Pain points | Product response |
| --- | --- | --- | --- |
| 律师 / 律师助理 | 快速阅读合同、证据和案件材料 | 文档多、格式杂、审查口径不稳定 | 深度审查流水线、风险矩阵、本地法律知识库、可追踪模型调用 |
| 中小企业法务 | 审查采购、租赁、劳动、服务合同 | 成本敏感、需要统一模板和审批依据 | 低价模型优先、条款替换建议、待补事实清单 |
| 个人用户 | 理解合同、借款、租赁、劳动争议材料 | 缺少法律背景、容易误解 AI 输出 | 免责声明、事实缺口提示、建议律师复核高风险结论 |

## Workflow Priorities

1. 文件进入系统后，先做格式识别、文本抽取和低价 OCR。
2. 对材料进行规则优先分类；只有不确定时调用低价分类模型。
3. 合同审查分阶段执行：预检、条款映射、风险识别、法律依据匹配、资深律师视角复核、可复制条款生成。
4. 输出报告必须包含风险位置、依据状态、待补事实、替代条款和免责声明。
5. 大 PDF 和复杂复核才升级到高级模型，避免所有请求默认走高价模型。

## Maintenance Signals to Track

- API 路由稳定性：`/api/v1/aihub/models` 返回的别名、默认模型和网关可用性。
- 成本指标：OCR/分类/审查/PDF 分析各阶段 token 用量和模型分布；当前可通过 `/api/v1/aihub/models/usage` 和前端 `/model-ops` 查看本进程内聚合数据。
- 运行时路由：`POST /api/v1/aihub/gentxt` 的 `task` 字段决定默认模型，超预算显式模型默认降级到任务推荐模型。
- 升级策略：`/api/v1/aihub/models` 的 `escalation_policy` 记录 cheap-first 起点、质量失败升级信号和隐私/提示注入硬停止规则。
- 回退链：`/api/v1/aihub/models` 的 `fallback_chains` 记录每个任务的 primary、verify、fallback 和 premium-exception 顺序，便于网关模型不可用时仍低价优先。
- 成本预测：`/api/v1/aihub/models` 的 `cost_forecast` 会对 cheap-first cascade 与 premium-only baseline 做月度成本对比。
- 成本守卫：`/api/v1/aihub/models` 的 `cost_guardrails` 会检查预算占用、失败率、premium 请求比例、未知价格模型和 cheap-first 节省目标。
- 路由回放：`/api/v1/aihub/models` 的 `routing_replay` 会用固定法律工作流场景检查 cheap-first 起点、premium 人工复核和硬停止是否发生漂移。
- 质量指标：JSON 解析失败率、OCR 空结果率、用户人工修正率、报告缺少原文定位的比例。
- 法律内容维护：本地法律知识库更新频率、引用校验失败项、需要人工复核的依据列表。
- 产品活跃度：上传文件数量、完成审查数量、案件工作台问答数量、用户中断率。
- 用户需求雷达：通过 `/api/v1/maintenance/user-needs` 查看当前需求优先级、外部研究来源、证据路径和发布门禁关联。
- 反馈路线图映射：通过 `/api/v1/maintenance/feedback-roadmap` 查看反馈类别如何映射到用户需求 ID 和发布门禁。
- 法律审查基准：通过 `/api/v1/maintenance/legal-review-benchmark` 检查合同风险识别、证据完整性、长 PDF 解析、隐私上传、提示注入和法律 RAG grounding 场景。

## Near-Term Maintenance Tasks

- 为模型路由增加单元测试，覆盖 `auto-fast`、`auto-review`、`auto-pdf` 和显式模型透传。
- 在后台仪表盘展示模型成本分布和失败重试情况，并逐步从进程内统计升级到持久化统计。
- 给深度审查报告增加用户反馈入口：有用、错误、需要律师复核、建议补充材料。
- 把反馈工单按用户需求 ID 聚类，优先处理“可追踪法律输出、隐私安全上传、文档解析质量、低价优先路由、提示注入韧性”这类高优先级需求。
- 在创建反馈工单前使用 triage-preview 的 `roadmap_alignment`，把反馈同步挂到对应 user need，避免重复的一次性修补。
- 每次模型路由、提示词、检索、报告结构或上传解析改动后，运行法律审查基准并把结果纳入发布准备记录。
- 为合同类型扩展专项策略：劳动合同、租赁合同、采购合同、服务合同、股权/投资协议。
- 定期检查 Gemini/NewAPI 网关模型名称变更，移除停用模型，更新 `.env.example` 和模型目录。
- 用 `model_runtime_router.py` 检查真实文本请求是否按任务选择模型，避免所有文本请求都落在同一默认路由。
- 根据法律审查基准和真实反馈调整 `model_escalation_policy.py`，但不要把 premium 模型设成高频任务默认值。
- 用 `model_cost_forecast.py` 复查高频任务的预计成本节省；当网关价格变化时同步更新模型目录和预测画像。
- 用 `model_cost_guardrails.py` 监控实际用量漂移，发现 premium 比例或未知价格模型异常时先修路由再增加预算。
- 用 `model_routing_replay.py` 在发布前回放典型场景，确认便宜模型优先策略没有被配置改动破坏。
- 用 `model_fallback_chains.py` 检查模型不可用、质量不足或需要人工复核时的下一步模型选择。

## Application-Safe Claim

申请开源支持或额度时，只应陈述已经落地的事实：本仓库正在维护一个法律文书审查和案件材料整理系统，已经包含 FastAPI 后端、React/Vite 前端、本地法律知识库、文件抽取、OCR、深度审查流水线和 OpenAI-compatible/Gemini 模型路由。不要声称已有大量外部 PR、issue triage 或正式 release，除非 GitHub 仓库中已经有对应记录。
