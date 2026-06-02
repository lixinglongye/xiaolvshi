# 律审雷达 v2.0 - 深度法律审查报告重构

## Design
- **Style**: Professional legal-tech, authoritative, trustworthy lawyer-grade report
- **Color Palette**: 
  - Primary Blue #1e40af (headers, navigation)
  - Slate #334155 (body text)
  - Critical Red #dc2626 (critical risk)
  - High Orange #ea580c (high risk)
  - Medium Amber #d97706 (medium risk)
  - Low Green #16a34a (low risk)
  - Legal Source Colors: Law Red #b91c1c, Admin Reg Orange #c2410c, Judicial Interp Orange #ea580c, Dept Rule Yellow #ca8a04, Local Reg Yellow #a16207, Guiding Case Blue #1d4ed8, Reference Case Sky #0284c7, Judgment Gray #6b7280, Template Gray #9ca3af, Commentary Gray #a1a1aa
  - Background #f8fafc, Card White #ffffff
- **Typography**: System font, bold section headings, clear hierarchy with numbered sections
- **Key Components**: 
  - Left sidebar TOC navigation with scroll-spy
  - Risk severity badges with icons
  - Legal effect badges (color-coded by source type)
  - Verification status badges (已校验/待核验/未检索到)
  - Three-version alternative clause tabs (保守/平衡/底线)
  - Collapsible risk detail cards with full legal analysis
  - Citation cards with authority level and applicability reason

## Development Tasks
- [x] Rewrite mockData.ts with deep lawyer-grade mock data (8+ risk items, legal analysis JSON, 3-version clauses, legal appendix)
- [x] Rewrite DeepReportPage.tsx with full report structure (cover, executive summary, contract structure, risk matrix, clause-by-clause analysis, missing clauses, favorable clauses, legal appendix, left TOC)
- [x] Add AI-powered upload form to DeepReportPage (document input, config, progress animation, API integration)
- [x] Create backend service (services/deep_review.py) with Agent Team system prompt calling claude-opus-4.6
- [x] Create backend router (routers/deep_review.py) with /analyze, /generate-document, /case-chat endpoints
- [x] Fix: Add document type pre-check (non-legal document detection) in deep_review service
- [x] Fix: Improve file upload handling and error messages in DeepReportPage
- [x] Fix: Clarify demo button label to avoid confusion with real AI analysis
- [x] Create frontend API client (lib/deepReviewApi.ts) for backend communication
- [x] Create report mapper (lib/reportMapper.ts) to convert AI response to frontend display format
- [x] Rewrite CaseDetailPage.tsx with left-right split layout (AI Chat left + Workspace right)
- [x] Create PipelineConfigPage.tsx for AI review pipeline (8 Agent stages)
- [x] Update App.tsx routes and Layout navigation
- [x] Lint and build check