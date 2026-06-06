# Case Workbench Risk Refresh Plan

`case-workbench-risk-refresh-plan` adds a metadata-only refresh plan to the
repository-backed case workbench runtime payload.

The plan consumes sanitized section state and recent state-event metadata from
the workbench runtime binding. It returns:

- section ids that should refresh live risk state;
- event ids and changed field names that affect risk or evidence graph state;
- blocking/review counts for tasks, deadlines, facts, and evidence graph gaps;
- privacy and claim boundaries showing that no write or notification happened.

It does not return raw event payloads, party names, client contact details,
document text, raw facts, raw evidence, prompts, model outputs, or credentials.
It also does not write risk state, refresh the evidence graph, send
notifications, complete lawyer review, or make legal advice claims.

The frontend case workbench runtime panel renders the plan as a compact
reviewer surface so maintainers can see which runtime deltas need follow-up
without exposing legal matter content.

Validation:

```bash
python -m pytest tests/test_case_workbench_risk_refresh_plan.py tests/test_case_workbench_runtime_binding.py tests/test_case_workbench_runtime_router.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```
