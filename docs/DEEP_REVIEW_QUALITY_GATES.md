# Deep Review Quality Gates

本项目的深度审查报告现在包含两个互补的质量字段：

- `quality_audit`：评分、警告和详细检查项，主要服务于报告可读性和交付成熟度。
- `quality_gate`：确定性的 pass/warn/fail 门禁，主要判断报告是否具备人工复核所需的最低结构证据。

## Gate Scope

`quality_gate` 不判断法律结论是否正确，也不替代执业律师复核。它只检查报告是否具备可审计结构：

| Gate | Fail/Warn | Meaning |
| --- | --- | --- |
| `risk-items-present` | fail | 报告必须至少包含一个结构化风险项。 |
| `risks-grounded` | fail | 每个风险项必须能定位到原文条款或具体问题位置。 |
| `high-risk-citations` | fail | 高/重大风险必须有已校验或至少可人工复核的引用。 |
| `revision-plans` | fail | 每个风险项必须有替换条款、修改方案或谈判策略。 |
| `pending-facts` | warn | 报告应列出待补事实，或明确说明没有待补事实。 |
| `legal-appendix` | warn | 报告应有法律依据附录，便于复核来源。 |
| `disclaimer` | fail | 报告必须声明 AI 辅助性质和非正式法律意见边界。 |

## Release Levels

- `ready_for_lawyer_spot_check`：所有门禁通过，可进入律师抽样复核。
- `lawyer_review_required`：存在 warning，必须由人工复核后再交付。
- `internal_draft_only`：存在 fail，只能作为内部草稿，不应交付给客户。

## Maintenance Usage

- API 返回报告时会自动附加 `quality_gate`。
- 前端深度报告页会展示门禁状态、分数、阻断 gate 和 warning gate。
- `app/backend/scripts/evaluate_deep_review_quality.py` 会在批量评估历史报告时输出 gate 状态。

## Security Boundary

质量门禁只读取报告结构字段，不记录 prompt、用户文档全文、API key、邮箱或上传文件名。
