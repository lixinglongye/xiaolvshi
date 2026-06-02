# legal_knowledge 模块

这个模块用于把法律检索从 prompt 里的零散常量升级成本地可维护知识库。

## 当前覆盖

- 数据源：`app/backend/data/legal_knowledge/contract_law_seed.json`
- 首批领域：合同审查
- 首批来源：国家法律法规数据库公布的《中华人民共和国民法典》
- 记录粒度：法条级记录，包含主题、关键词、条文要点、审查摘要、风险提示、官方来源、校验状态和效力状态

## 入库

在 `app/backend` 目录执行：

```powershell
python scripts/update_legal_knowledge.py
```

只看差异不写入：

```powershell
python scripts/update_legal_knowledge.py --dry-run
```

指定其他 seed 文件：

```powershell
python scripts/update_legal_knowledge.py --seed-path data/legal_knowledge/contract_law_seed.json
```

## 定期更新

这个脚本设计成幂等 upsert，可以交给 Windows Task Scheduler、cron 或 CI 定时执行。每次运行会写入：

```text
app/backend/logs/legal_knowledge_update.jsonl
```

需要常驻轮询时：

```powershell
python scripts/update_legal_knowledge.py --watch --interval-hours 24
```

## 检索接口

- `GET /api/v1/legal-knowledge/search?q=违约金&domain=合同审查`
- `GET /api/v1/legal-knowledge/sources/CIVIL-585`
- `GET /api/v1/legal-knowledge/stats`
- `POST /api/v1/legal-knowledge/admin/seed`

后续扩展诉讼、劳动、公司、借贷、知识产权时，新建对应 JSON seed 文件即可复用同一张表和接口。推荐新增字段沿用 `legal_domain`、`topics`、`keywords`、`authority_level`，避免不同领域检索结果不可比较。
