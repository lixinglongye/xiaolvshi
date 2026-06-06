# ModelOps Cheap-First Priority Queue

## Purpose

The cheap-first priority queue ranks ModelOps work for Gemini/NewAPI default-model optimization. It is an operator-facing triage view, not an automatic model promotion mechanism.

## Inputs

The queue consumes existing metadata-only evidence:

- default optimization recommendations
- Gemini cheap-first coverage gate rows
- route quality budget rows
- default change queue items
- cheap-first release decision status
- price refresh and catalog source audit status

## Output

Each priority item includes:

- task and env var metadata
- current, recommended, and cheap-start model ids
- priority rank, score, label, and risk level
- release, queue, coverage, default optimization, and route-quality statuses
- estimated monthly savings when pricing metadata is available
- reason codes and next action
- per-item validation commands

## Boundaries

This evidence is metadata-only. It does not:

- write environment files or runtime configuration
- call NewAPI, Gemini, OpenAI, Google, or any gateway
- run probes or shift traffic
- include prompts, raw payloads, raw legal text, raw model output, credentials, or emails
- claim public benchmark scores
- claim 24h completion or 100-update completion

## Validation

```powershell
cd app/backend
python -m pytest tests/test_model_ops_cheap_first_priority_queue.py tests/test_model_ops_readiness.py tests/test_model_ops_default_change_queue.py tests/test_model_route_quality_budget.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```
