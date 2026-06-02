# Deep Review Release Decision

深度审查报告新增 `release_decision` 字段，把质量门禁、引用审计、证据审计和风险评分汇总为一个可操作的交付结论。

## Purpose

此前报告会分别返回：

- `quality_gate`
- `citation_audit`
- `evidence_audit`
- `risk_scoring`
- `delivery_audit`
- `human_review_workflow`

这些字段分别有用，但运营人员和律师仍需要自己判断报告到底能否交付。`release_decision` 提供统一结论：

- 是否只能作为内部草稿。
- 是否必须律师复核。
- 是否可进入律师抽检后交付。
- 当前阻断项、警告项和必做动作。

## Status

| Status | Release Level | Meaning |
| --- | --- | --- |
| `blocked` | `internal_draft_only` | 质量、引用或证据审计存在 fail，只能内部使用。 |
| `lawyer_review_required` | `lawyer_review_required` | 没有阻断项，但仍有 warning 或高风险压力，交付前必须复核。 |
| `ready_for_spot_check` | `ready_for_lawyer_spot_check` | 可进入律师抽检和客户交付流程。 |

## Report Fields

```json
{
  "schema_version": "release-decision-v1",
  "status": "lawyer_review_required",
  "release_level": "lawyer_review_required",
  "readiness_score": 84,
  "client_delivery_allowed": false,
  "lawyer_review_required": true,
  "triage_level": "elevated",
  "blocking_reasons": [],
  "warning_reasons": [
    "Evidence audit requires pending fact or evidence-plan follow-up."
  ],
  "required_actions": [
    "Resolve blocking pending facts: PF-001"
  ],
  "decision_factors": {
    "quality_gate_status": "pass",
    "citation_audit_status": "warn",
    "evidence_audit_status": "warn",
    "risk_score": 86,
    "risk_level": "high",
    "critical_risk_count": 2,
    "high_risk_count": 3
  }
}
```

## Scoring

`readiness_score` 是交付就绪分，不等同于法律风险分：

- `quality_gate.score` 权重 35%。
- `citation_audit.score` 权重 25%。
- `evidence_audit.score` 权重 25%。
- 风险压力控制分权重 15%。

如果质量、引用或证据审计失败，会额外扣分并强制 `blocked`。

## Maintenance Hooks

- 后端服务：`app/backend/services/release_decision.py`
- 报告接入：`app/backend/services/deep_review.py`
- 前端展示：`app/frontend/src/pages/DeepReportPage.tsx`
- 单元测试：`app/backend/tests/test_release_decision.py`
