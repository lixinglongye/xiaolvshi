# 项目结构整理

本文档说明当前项目目录边界、核心模块和后续扩展位置。原则是先把结构边界清楚化，不移动已经被自动路由、构建工具和运行脚本依赖的源码路径。

## 顶层目录

```text
D:\小律师
├── app/                      # 主应用代码
│   ├── backend/              # FastAPI 后端
│   └── frontend/             # React/Vite 前端
├── assets/                   # 视觉资产和图片素材
├── docs/                     # 项目级文档
├── uploads/                  # 用户上传/需求输入文件，本地运行产物
├── .wiki.md                  # 旧版项目摘要
├── README.md                 # 项目入口说明
└── todo.md                   # 迭代记录
```

`uploads/`、日志、数据库、构建产物、截图输出都属于本地运行产物，不应与源码混在一起看；已通过根目录 `.gitignore` 隔离。

## 后端结构

```text
app/backend
├── main.py                   # FastAPI 应用入口，自动扫描 routers
├── core/                     # 配置、数据库、加密等基础设施
├── routers/                  # HTTP API 层
├── services/                 # 业务逻辑和算法编排
├── models/                   # SQLAlchemy ORM 模型
├── schemas/                  # Pydantic 响应/请求模型
├── data/                     # 运行所需静态数据和 seed
├── scripts/                  # 本地维护脚本、定期更新脚本
├── docs/                     # 后端模块文档
├── alembic/                  # 数据库迁移
├── mock_data/                # 演示数据
├── data_models/              # 生成式实体配置遗留目录
├── logs/                     # 后端运行日志，本地产物
└── dev.db                    # 本地 SQLite 数据库，本地产物
```

### 后端关键模块

```text
services/deep_review.py          # 深度法律审查主流程，多阶段分析和报告组装
services/document_extraction.py  # PDF/Word/文本解析，OCR 兜底
services/document_strategy.py    # 不同法律文件类型的专门审查策略
services/legal_research.py       # 本地法律依据检索，供报告引用使用
services/legal_knowledge.py      # 法律知识库 seed、upsert、检索服务
services/aihub.py                # OpenAI-compatible 模型网关封装
services/storage.py              # 外部对象存储服务
```

### legal_knowledge 模块

```text
models/legal_knowledge.py
schemas/legal_knowledge.py
services/legal_knowledge.py
routers/legal_knowledge.py
data/legal_knowledge/contract_law_seed.json
scripts/update_legal_knowledge.py
docs/legal_knowledge.md
```

当前首批覆盖合同审查高频《民法典》法条。后续扩展诉讼、劳动、公司、借贷、知识产权时，优先新增 JSON seed 文件，再复用 `LegalKnowledgeService` 的 upsert 和检索接口。

## 前端结构

```text
app/frontend
├── src/
│   ├── App.tsx               # 路由入口
│   ├── main.tsx              # React 挂载入口
│   ├── pages/                # 页面级组件
│   ├── components/           # 业务组件和 shadcn/ui 基础组件
│   ├── lib/                  # API 客户端、数据映射、工具函数
│   ├── api/                  # 少量独立 API 封装
│   ├── contexts/             # React Context
│   └── hooks/                # 通用 hooks
├── public/                   # 静态资源
├── docs/                     # 前端架构和图
├── prerender/                # 预渲染脚本
├── dist/                     # 构建产物，本地产物
└── output/                   # Playwright 截图输出，本地产物
```

### 前端关键模块

```text
src/pages/UploadPage.tsx         # 文档上传
src/pages/DeepReportPage.tsx     # 深度审查报告页
src/pages/GeneratePage.tsx       # 法律文书生成
src/pages/CaseDetailPage.tsx     # 案件工作台
src/lib/deepReviewApi.ts         # 深度审查 API 客户端
src/lib/reportMapper.ts          # 后端报告结构到前端展示结构映射
src/components/Layout.tsx        # 主导航和页面框架
```

## 运行产物边界

以下目录和文件不属于源码：

```text
app/backend/.venv/
app/backend/__pycache__/
app/backend/services/__pycache__/
app/backend/logs/
app/backend/dev.db
app/frontend/node_modules/
app/frontend/dist/
app/frontend/output/
uploads/
```

这些内容可以在本地存在，但不应作为架构阅读重点，也不应进入版本库。

## 后端 API 分层约定

```text
routers/   只处理 HTTP 参数、状态码、依赖注入
services/  放业务流程、算法、外部服务调用
models/    放数据库表结构
schemas/   放 Pydantic 输入输出结构
data/      放可复用 seed 和本地知识资源
scripts/   放人工或定时维护脚本
docs/      放模块设计说明
```

新增后端模块时，推荐按这个顺序落地：

```text
models/<module>.py
schemas/<module>.py
services/<module>.py
routers/<module>.py
docs/<module>.md
```

如果模块需要本地知识或模板，再增加：

```text
data/<module>/
scripts/<module>_*.py
```

## 当前优先级建议

1. 法律算法继续向 `services/deep_review.py`、`document_strategy.py`、`legal_research.py`、`legal_knowledge.py` 收敛，不再把法律规则散落到页面 mock 数据里。
2. 新增领域知识库时只扩展 `data/legal_knowledge/*.json`，避免继续扩大硬编码常量。
3. 前端页面继续保留在 `src/pages/`，通用展示组件再沉淀到 `src/components/`。
4. 运行产物不要手动整理到源码目录；日志、截图、数据库、上传文档都已列入 `.gitignore`。
