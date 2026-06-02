# Document Review Preflight

Deep review now has a deterministic preflight stage that runs before expensive model calls.

## Purpose

The service answers four questions without calling an AI model:

- Is the supplied text reviewable as a legal document?
- Which `document_strategy` best matches the text and declared document type?
- Which strategy-required facts appear missing?
- Should the next stage use cheap-first, balanced review, or premium-exception routing?

## Endpoint

```http
POST /api/v1/deep-review/preflight
```

Request:

```json
{
  "document_text": "甲方与乙方签订服务合同...",
  "document_type": "服务合同",
  "user_role": "甲方",
  "review_goal": "签署前审查",
  "known_facts": ["合同尚未签署"],
  "extraction": {"page_count": 8}
}
```

Response fields:

- `status`: `ready`, `needs_context`, or `blocked`.
- `strategy`: selected review strategy from `document_strategy.py`.
- `document_signals`: text length, legal markers, complexity signals, and complexity score.
- `routing`: recommended task and model budget decision.
- `missing_required_facts`: fields the selected strategy expects but did not find.
- `blocking_reasons`, `warning_reasons`, and `recommended_actions`.

## Cost policy

- Simple documents start on `fast` / cheap-first routing.
- Moderate documents move to balanced `review` routing.
- Very long or complex documents move to `pdf` / premium-exception routing and should be operator-reviewed before spending premium budget.

The preflight result is attached to `report.preflight` and `report.report_meta.preflight_status` for generated deep-review reports.
