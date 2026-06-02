# Deep Review Citation Audit

深度审查报告新增 `citation_audit` 字段，用确定性规则检查法律依据和风险项引用是否足够可复核。它不判断法律结论是否正确，而是判断来源结构、引用覆盖和高风险引用是否具备人工复核基础。

## What It Checks

- 报告是否包含 `legal_authority_appendix`。
- 风险项是否有引用，尤其是高/重大风险。
- 引用的 `source_id` 是否能在法律依据附录中找到。
- 来源是否具备 `source_name`、`source_type`、`authority_level` 等可复核字段。
- 来源是否已核验，或至少有较高置信度和完整元数据。
- 附录中是否有重复 source ID、孤立来源或弱元数据来源。

## Report Fields

`citation_audit` 示例：

```json
{
  "schema_version": "citation-audit-v1",
  "status": "warn",
  "score": 82,
  "source_count": 6,
  "citation_count": 9,
  "risk_count": 9,
  "cited_risk_count": 8,
  "verified_source_count": 4,
  "reviewable_source_count": 6,
  "verified_ratio": 0.67,
  "reviewable_ratio": 1.0,
  "risk_citation_coverage": 0.89,
  "high_risk_without_reviewable_citation": [],
  "high_risk_without_verified_citation": ["R-003"],
  "weak_source_ids": [],
  "missing_appendix_source_ids": [],
  "duplicate_source_ids": [],
  "recommended_actions": [
    "Verify cited authorities for high-risk items: R-003"
  ]
}
```

## Status Rules

| Status | Meaning |
| --- | --- |
| `pass` | 来源存在，高风险引用可复核，弱来源和附录缺口均可控。 |
| `warn` | 有来源但存在未核验、弱元数据、缺失附录来源或核验比例偏低。 |
| `fail` | 无法律依据附录，或高/重大风险缺少可复核引用。 |

## Relationship To Other Checks

- `quality_gate`：判断报告是否可进入人工复核/交付流程。
- `risk_scoring`：判断风险严重程度和排序。
- `citation_audit`：判断引用和法律依据是否足够可复核。

三者互补：一个高分风险项仍可能因为引用审计 `warn` 或 `fail` 而被要求律师补充核验。

## Maintenance Hooks

- 后端服务：`app/backend/services/citation_audit.py`
- 报告接入：`app/backend/services/deep_review.py`
- 摘要接口：`app/backend/routers/deep_review.py`
- 前端展示：`app/frontend/src/pages/DeepReportPage.tsx`
- 单元测试：`app/backend/tests/test_citation_audit.py`
