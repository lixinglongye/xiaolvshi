# Frontend UI Regression Gate

This gate records metadata-only evidence for the two reviewer-facing UI surfaces
that carry the most maintenance and model-ops claims:

- `/maintenance`
- `/model-ops`

The gate is intentionally conservative. It verifies that the project has
executable frontend commands for:

- `npm run lint`
- `npm run typecheck`
- `npm run build`
- `npm run ui:regression`

It also tracks which panels still need mocked page-level regression tests. The
current gate does not claim that every UI state is automated. It records the gap
so release reviewers can distinguish runnable frontend checks from missing
browser-level assertions.

## Covered Risk Areas

The `/maintenance` page carries evidence for:

- partial evidence failure handling
- user-need benchmark coverage
- legal-document benchmark coverage
- continuous update ledger
- Gemini/NewAPI selector evidence

The `/model-ops` page carries evidence for:

- cheap-first calibration
- ModelOps load guard
- Performance observations
- Gemini catalog source audit
- Cheap-first release decision
- Default change queue
- Cheap-first canary plan
- Cheap-first canary observation review
- Cheap-first canary promotion decision
- Cheap-first canary approval packet
- Cheap-first quality budget
- selector replay
- route telemetry
- route telemetry remediation
- gateway probe evaluation

## Required Commands

Run these before claiming the frontend evidence pages are reviewable:

```powershell
cd app/frontend
npm run lint
npm run typecheck
npm run build
npm run ui:regression
```

Run this backend metadata gate test after changing the evidence contract:

```powershell
cd app/backend
python -m pytest tests/test_frontend_ui_regression_gate.py -q
```

## Non-Claims

This gate does not:

- run a live browser by itself
- replace future browser-level network-mocked regression tests
- prove public benchmark scores
- prove production model routing health
- return source code, raw browser storage, raw model output, credentials, or user
  legal text
- replace future mocked `/maintenance` and `/model-ops` page regression tests

## Next Automation Targets

The current `ui:regression` script is a dependency-free source-contract check.
The next frontend testing layer should mock API responses in a browser and
assert:

- all evidence panels render on success
- one failing maintenance endpoint shows the partial-load banner while other
  panels remain visible
- raw fixture snippets, credentials, and raw model outputs are never rendered
- cheap-first and route telemetry warnings remain visible in model-ops scenarios
