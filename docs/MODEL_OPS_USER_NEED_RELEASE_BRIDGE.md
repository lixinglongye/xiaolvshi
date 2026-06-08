# ModelOps User-Need Release Bridge

`model_ops_user_need_release_bridge.py` connects product user-need evidence to
cheap-first ModelOps release review. It joins:

- `user_need_implementation_priority_queue`
- `user_need_gemini_route_coverage`
- local user-need benchmark coverage metadata

The bridge is metadata-only. It does not call NewAPI, Gemini, OpenAI, Google,
gateways, or public datasets. It does not write configuration, shift traffic, or
return raw legal text, benchmark samples, prompts, model outputs, payloads,
emails, identifiers, or credentials.

## Release Rules

- High-priority user needs block default changes when implementation evidence is
  blocked or Gemini route coverage is blocked or unmapped.
- Medium and low priority implementation blockers remain `review_required`.
- Public benchmark license review, premium exception review, partial local
  coverage, and route-hint calibration gaps remain maintainer-review signals.
- Ready rows support current cheap-first defaults, but the bridge never changes
  production routes by itself.

## ModelOps Wiring

The bridge is exposed in:

- `/api/v1/aihub/models`
- `/api/v1/aihub/models/user-need-release-bridge`
- `cheap_first_release_decision` as the required signal
  `user_need_release_bridge`
- `model_ops_readiness` as the release-evidence component
  `user-need-release-bridge`
- the `/model-ops` UI between `Cheap-first release decision` and
  `Default change queue`

## Validation

```bash
python -m pytest tests/test_model_ops_user_need_release_bridge.py tests/test_user_need_implementation_priority_queue.py tests/test_user_need_gemini_route_coverage.py -q
python -m pytest tests/test_model_ops_cheap_first_release_decision.py tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```
