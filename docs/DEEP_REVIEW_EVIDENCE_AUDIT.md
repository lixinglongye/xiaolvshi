# Deep Review Evidence Audit

深度审查报告新增 `evidence_audit` 字段，用确定性规则检查风险项是否具备证据保存/举证计划，以及待补事实是否会阻断交付。

## What It Checks

- 每个风险项是否有 `legal_analysis.evidence_suggestion`。
- 高/重大风险是否缺少证据计划。
- `professional_review_framework.evidence_checklist` 是否提供事项级证据清单。
- `pending_facts` 是否包含会影响风险等级、合同效力、举证责任或交付稳定性的关键事实。
- 证据建议是否过度重复，导致输出不够针对具体风险。

## Report Fields

`evidence_audit` 示例：

```json
{
  "schema_version": "evidence-audit-v1",
  "status": "warn",
  "score": 84,
  "risk_count": 9,
  "risk_with_evidence_count": 8,
  "risk_evidence_coverage": 0.89,
  "evidence_suggestion_count": 18,
  "framework_evidence_count": 6,
  "pending_fact_count": 4,
  "blocking_pending_fact_count": 1,
  "risks_without_evidence_plan": ["R-009"],
  "high_risk_without_evidence_plan": [],
  "blocking_pending_fact_ids": ["PF-001"],
  "recommended_actions": [
    "Resolve blocking pending facts: PF-001"
  ]
}
```

## Status Rules

| Status | Meaning |
| --- | --- |
| `pass` | 大部分风险有证据计划，且没有阻断性待补事实。 |
| `warn` | 存在阻断事实、证据覆盖不足或缺少事项级证据清单。 |
| `fail` | 高/重大风险缺少证据计划。 |

## Relationship To Other Checks

- `risk_scoring` 排序风险严重程度。
- `citation_audit` 检查法律依据和引用是否可复核。
- `evidence_audit` 检查事实和证据链是否足以支撑交付。
- `quality_gate` 决定报告是否能进入人工复核或只能作为内部草稿。

## Maintenance Hooks

- 后端服务：`app/backend/services/evidence_audit.py`
- 报告接入：`app/backend/services/deep_review.py`
- 前端展示：`app/frontend/src/pages/DeepReportPage.tsx`
- 单元测试：`app/backend/tests/test_evidence_audit.py`
