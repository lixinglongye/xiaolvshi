# Deep Review Risk Scoring

深度审查报告新增 `risk_scoring` 字段，用确定性规则为报告和每个风险项生成 0-100 分。该评分用于风险排序、摘要展示和数据库 `risk_score` 持久化，不依赖额外模型调用。

## Goals

- 稳定排序：同一份结构化报告在相同输入下得到相同风险分和排序。
- 可解释：每个风险项暴露等级、严重性、发生概率、引用、原文定位和修改方案完整性等评分因子。
- 可测试：评分服务是纯确定性逻辑，后端单元测试可以覆盖回归。
- 可维护：评分结果写入完整报告 JSON、单项风险、前端展示和 `review_reports.risk_score`。

## Report Fields

`risk_scoring` 示例：

```json
{
  "schema_version": "risk-scoring-v1",
  "overall_score": 86,
  "overall_level": "high",
  "risk_count": 9,
  "counts": {
    "critical": 2,
    "high": 3,
    "medium": 3,
    "low": 1
  },
  "top_risk_ids": ["R-001", "R-002", "R-003"],
  "score_distribution": {
    "max": 93,
    "average": 68.4,
    "top3_average": 85.3
  },
  "risk_scores": [
    {
      "risk_id": "R-001",
      "score": 93,
      "score_level": "critical",
      "priority_rank": 1,
      "citation_score": 92,
      "grounding_score": 100,
      "revision_score": 100,
      "evidence_confidence_score": 96,
      "penalty": 0
    }
  ]
}
```

每个 `risk_items[]` 也会附加：

- `risk_score`
- `risk_score_rank`
- `risk_score_level`
- `risk_score_explanation`
- `evidence_confidence_score`

## Formula

单项风险基础分：

```text
base_score = risk_level * 0.50 + severity * 0.30 + probability * 0.20
```

基础维度映射：

| Dimension | critical / very high | high | medium | low | unknown |
| --- | ---: | ---: | ---: | ---: | ---: |
| risk level | 100 | 78 | 52 | 24 | - |
| severity / probability | 95 | 78 | 52 | 24 | 45 |

扣分项：

| Condition | Penalty |
| --- | ---: |
| 缺少原文定位或问题定位 | 5 |
| 高/重大风险缺少可复核引用 | 4 |
| 缺少修改方案或替代条款 | 3 |

整体报告分综合最高风险、Top 3 风险均值、全部风险均值和风险数量压力：

```text
overall_score = top_score * 0.55 + top3_average * 0.30 + average * 0.15 + count_pressure
```

## Quality Gate Boundary

`risk_scoring` 和 `quality_gate` 分工不同：

- `risk_scoring`：判断风险严重程度和排序。
- `quality_gate`：判断报告是否具备可交付、可复核的最低结构证据。

因此，低质量引用会影响单项证据信心和少量扣分，但不会把一个重大商业/法律风险简单降级为低风险。阻断交付仍由 `quality_gate` 负责。

## Maintenance Hooks

- 后端服务：`app/backend/services/risk_scoring.py`
- 报告接入：`app/backend/services/deep_review.py`
- 持久化字段：`app/backend/routers/deep_review.py`
- 前端展示：`app/frontend/src/pages/DeepReportPage.tsx`
- 单元测试：`app/backend/tests/test_risk_scoring.py`
