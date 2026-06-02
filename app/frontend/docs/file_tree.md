# 律审雷达 项目文件结构

```
app/
├── backend/
│   ├── main.py                          # FastAPI 入口
│   ├── core/
│   │   ├── config.py                    # 配置
│   │   ├── database.py                  # 数据库连接
│   │   ├── enums.py                     # 枚举定义（新增法律来源类型、效力等级等）
│   │   ├── auth.py                      # 认证
│   │   └── mask_crypto.py              # 脱敏加密
│   ├── models/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── base.py
│   │   ├── documents.py
│   │   ├── review_reports.py           # 扩展：新增字段
│   │   ├── clauses.py                  # 【新增】条款切分表
│   │   ├── risk_items.py               # 扩展：新增字段
│   │   ├── legal_sources.py            # 扩展：新增字段
│   │   ├── source_citations.py         # 扩展：新增字段
│   │   ├── cases.py                    # 扩展：新增字段
│   │   ├── case_parties.py
│   │   ├── case_materials.py           # 扩展：新增字段
│   │   ├── case_facts.py              # 扩展：新增字段
│   │   ├── evidences.py               # 扩展：新增字段
│   │   ├── generated_documents.py     # 扩展：新增字段
│   │   ├── case_tasks.py             # 扩展：新增字段
│   │   ├── orders.py
│   │   ├── organizations.py
│   │   ├── organization_members.py
│   │   ├── audit_logs.py
│   │   ├── feedback_tickets.py
│   │   └── deletion_requests.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── ai_review.py               # 重构：深度审查 + 案件文书生成 + AI Chat
│   │   ├── ai_deep_review.py          # 【新增】深度审查专用路由
│   │   ├── ai_case_chat.py            # 【新增】案件 AI Chat 路由
│   │   ├── ai_case_documents.py       # 【新增】案件文书生成路由
│   │   ├── clauses.py                 # 【新增】条款 CRUD
│   │   ├── documents.py
│   │   ├── review_reports.py
│   │   ├── risk_items.py
│   │   ├── legal_sources.py
│   │   ├── source_citations.py
│   │   ├── cases.py
│   │   ├── case_parties.py
│   │   ├── case_materials.py
│   │   ├── case_facts.py
│   │   ├── evidences.py
│   │   ├── generated_documents.py
│   │   ├── case_tasks.py
│   │   ├── orders.py
│   │   ├── payments.py
│   │   ├── storage.py
│   │   ├── settings.py
│   │   ├── health.py
│   │   ├── user.py
│   │   ├── audit_logs.py
│   │   ├── feedback_tickets.py
│   │   ├── deletion_requests.py
│   │   ├── organizations.py
│   │   ├── organization_members.py
│   │   └── templates.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_deep_review.py          # 【新增】深度审查服务（8 Agent 编排）
│   │   ├── ai_case_chat.py            # 【新增】案件 Chat 服务
│   │   ├── ai_case_documents.py       # 【新增】案件文书生成服务
│   │   ├── clauses.py                 # 【新增】条款服务
│   │   ├── documents.py
│   │   ├── reviews.py
│   │   ├── risk_items.py
│   │   ├── legal_sources.py
│   │   ├── source_citations.py
│   │   ├── cases.py
│   │   ├── case_materials.py
│   │   ├── case_facts.py
│   │   ├── case_parties.py
│   │   ├── case_tasks.py
│   │   ├── evidences.py
│   │   ├── generated_documents.py
│   │   ├── orders.py
│   │   ├── payment.py
│   │   ├── storage.py
│   │   ├── audit_logs.py
│   │   ├── mock_data.py               # 扩展：深度模拟数据
│   │   └── user.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── aihub.py
│   │   ├── storage.py
│   │   ├── deep_review.py             # 【新增】深度审查请求/响应 Schema
│   │   ├── case_chat.py               # 【新增】案件 Chat Schema
│   │   └── case_documents.py          # 【新增】案件文书生成 Schema
│   ├── mock_data/
│   │   ├── legal_sources.json          # 扩展：完整法律来源库
│   │   ├── deep_review_report.json     # 【新增】深度审查报告模拟数据
│   │   └── templates.json
│   └── data_models/
│       ├── clauses.json                # 【新增】
│       └── ... (已有 data_models)
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                     # 路由配置（新增 pipeline-config 路由）
│   │   ├── pages/
│   │   │   ├── Index.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── UploadPage.tsx
│   │   │   ├── ReviewProgressPage.tsx
│   │   │   ├── ReportPage.tsx
│   │   │   ├── DeepReportPage.tsx      # 【重构】完整深度报告页
│   │   │   ├── CasesPage.tsx
│   │   │   ├── NewCasePage.tsx
│   │   │   ├── CaseDetailPage.tsx      # 【重构】左右分栏工作台
│   │   │   ├── PipelineConfigPage.tsx  # 【新增】AI 审查流水线配置
│   │   │   ├── GeneratePage.tsx
│   │   │   ├── DocumentsPage.tsx
│   │   │   ├── TeamPage.tsx
│   │   │   ├── SettingsPage.tsx
│   │   │   ├── AdminPage.tsx
│   │   │   ├── PricingPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── SignupPage.tsx
│   │   │   └── ...
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── AuthGuard.tsx
│   │   │   ├── DisclaimerBanner.tsx
│   │   │   ├── deep-report/            # 【新增】深度报告组件目录
│   │   │   │   ├── ReportSidebar.tsx
│   │   │   │   ├── ReportCover.tsx
│   │   │   │   ├── ExecutiveSummary.tsx
│   │   │   │   ├── ContractSummary.tsx
│   │   │   │   ├── RiskMatrixTable.tsx
│   │   │   │   ├── RiskItemDetailCard.tsx
│   │   │   │   ├── LegalAnalysisBlock.tsx
│   │   │   │   ├── CitationCard.tsx
│   │   │   │   ├── AlternativeClauseTabs.tsx
│   │   │   │   ├── MissingClauseSection.tsx
│   │   │   │   ├── FavorableClauseSection.tsx
│   │   │   │   ├── PendingFactsSection.tsx
│   │   │   │   ├── LegalAuthorityAppendix.tsx
│   │   │   │   └── ReportActions.tsx
│   │   │   ├── case-workspace/         # 【新增】案件工作台组件目录
│   │   │   │   ├── CaseInfoCard.tsx
│   │   │   │   ├── AIChatPanel.tsx
│   │   │   │   ├── ChatMessageList.tsx
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   ├── WorkspaceTabs.tsx
│   │   │   │   ├── DocumentsTab.tsx
│   │   │   │   ├── GenerateDocDialog.tsx
│   │   │   │   ├── DocDetailModal.tsx
│   │   │   │   ├── MaterialsTab.tsx
│   │   │   │   ├── EvidenceTab.tsx
│   │   │   │   ├── TimelineTab.tsx
│   │   │   │   ├── TasksTab.tsx
│   │   │   │   └── StrategyTab.tsx
│   │   │   ├── shared/                 # 【新增】共享组件
│   │   │   │   ├── LegalEffectBadge.tsx
│   │   │   │   ├── VerificationStatusBadge.tsx
│   │   │   │   ├── RiskLevelBadge.tsx
│   │   │   │   ├── CopyButton.tsx
│   │   │   │   ├── CitationLink.tsx
│   │   │   │   └── LawyerReviewButton.tsx
│   │   │   └── ui/                     # Shadcn-ui 组件（已有）
│   │   ├── api/
│   │   │   ├── deep-review.ts          # 【新增】深度审查 API 调用
│   │   │   ├── case-chat.ts            # 【新增】案件 Chat API 调用
│   │   │   ├── case-documents.ts       # 【新增】案件文书生成 API 调用
│   │   │   └── ... (已有 API 模块)
│   │   ├── contexts/
│   │   │   ├── AuthContext.tsx
│   │   │   └── I18nContext.tsx
│   │   ├── hooks/
│   │   │   ├── useDeepReport.ts        # 【新增】深度报告 Hook
│   │   │   ├── useCaseChat.ts          # 【新增】案件 Chat Hook
│   │   │   └── ... (已有 Hooks)
│   │   └── lib/
│   │       └── utils.ts
│   ├── docs/
│   │   ├── system_design.md            # 本文档
│   │   ├── architect.plantuml
│   │   ├── class_diagram.plantuml
│   │   ├── sequence_diagram.plantuml
│   │   ├── er_diagram.plantuml
│   │   └── file_tree.md
│   └── public/
│       └── ...
```