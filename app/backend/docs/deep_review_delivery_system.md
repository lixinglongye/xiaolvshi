# Deep Review Delivery System

本项目的深度审查不应定位为普通 LLM Chat，而应定位为法律审查 SaaS 交付系统。

## 交付契约

- 文书必须先进入 Intake、文书类型策略、条款切分、规则预扫描、风险识别、法律检索、引用校验、律师复核、条款改写和报告组装。
- 每个风险项必须尽量包含原文定位、风险等级、用户影响、相对方抗辩、法院/仲裁关注点、举证责任、证据建议和替代条款。
- 法律依据只有命中本地知识库或权威来源后才能标记为“已校验”；模型自行给出的依据必须标记“待核验”。
- 报告必须生成质量审计、交付审计和人工复核任务包，便于进入律师/法务复核流程。

## 当前核心护栏

- `DocumentReviewStrategy`：针对租赁、劳动、买卖、服务、借贷、担保、股权、诉讼、答辩、律师函、仲裁申请分别配置必备字段、风险规则、证据清单和律师复核触发项。
- `LocalLegalResearchService`：本地法条与实务清单检索，并按文书类型降低错域引用。
- `quality_audit`：检查原文定位、已校验引用、替代条款、模板化有利条款、法律附录完整性和文书策略覆盖。
- `delivery_audit`：判断报告是否可进入客户交付前抽检、律师复核或仅能作为内部初稿。
- `human_review_workflow`：把 AI 初稿转成律师/法务可执行的复核任务。

## 回归评测

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_deep_review_quality.py --report-id 6
.\.venv\Scripts\python.exe scripts\evaluate_deep_review_quality.py --fail-on-low --min-score 70
```

后续每扩展一个文书类型或法条库，应增加对应样本报告并跑上述评测，重点关注：

- 高/重大风险是否有已校验依据；
- 有利条款是否仍出现模板化原因或建议；
- 法律依据附录是否有条号和正文摘录；
- 替代条款三版本是否为空或占位；
- 文书策略必备字段是否被正确识别为待补事实。
