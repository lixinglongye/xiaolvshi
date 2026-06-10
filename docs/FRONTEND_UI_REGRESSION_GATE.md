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
- legal-document benchmark route-plan execution readiness
- legal benchmark research refresh
- model route legal benchmark risk queue
- legal RAG authority citation gate
- legal RAG hallucination triage gate
- small legal document benchmark runbook evidence
- continuous update ledger
- Gemini/NewAPI selector evidence

The `/model-ops` page carries evidence for:

- cheap-first calibration
- ModelOps load guard
- Performance observations
- Gemini catalog source audit
- Gemini official cheap-first source review
- Gemini official model family roadmap evidence
- Cheap-first release decision
- Default change queue
- Cheap-first canary plan
- Cheap-first canary observation review
- Cheap-first canary promotion decision
- Cheap-first canary approval packet
- Cheap-first canary rollback drill
- Cheap-first quality budget
- Gateway request compatibility gate
- AIHub media/speech default catalog gate
- AIHub media runtime compatibility gate
- Gemini embedding cheap-first preflight
- selector replay
- route telemetry
- route telemetry repository
- route telemetry result archive
- route telemetry cost ledger
- route telemetry ops summary
- route telemetry triage queue
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
- download benchmark datasets, import external legal text, call models, or expose
  credentials for legal benchmark research refresh evidence
- call gateways, write model routes, expose raw route payloads, download datasets,
  or claim benchmark performance for the model route legal benchmark risk queue
- call NewAPI, Gemini, gateways, download datasets, expose raw legal text,
  prompts, model outputs, or credentials for the Legal RAG authority citation
  gate
- call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or
  the network, download public benchmark datasets, expose raw legal text,
  snippets, generated text, prompts, model outputs, gateway payloads, or
  credentials, or claim public benchmark scores, production legal quality, or
  client delivery for the small legal document benchmark runbook evidence
- call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or
  the network, write configuration, change defaults, or expose request bodies,
  response bodies, headers, prompts, raw payloads, legal text, model outputs,
  emails, or credentials for the Gemini official model family roadmap evidence
- call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or
  the network, write configuration, change defaults, shift traffic, claim live
  pricing accuracy, claim automatic default changes, or expose API keys,
  Authorization headers, request bodies, response bodies, prompts, raw payloads,
  legal text, model outputs, emails, or credentials for the Gemini official
  cheap-first source review
- call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or
  the network, write configuration, change defaults, shift traffic, or expose
  request bodies, response bodies, headers, prompts, raw payloads, audio,
  transcripts, legal text, model outputs, gateway responses, emails,
  credentials, or user identifiers for the AIHub media/speech default catalog
  gate
- call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or
  the network, write configuration, change defaults, shift traffic, or expose
  request bodies, response bodies, headers, prompts, raw payloads, audio,
  transcripts, legal text, model outputs, gateway responses, emails,
  credentials, or user identifiers for the AIHub media runtime compatibility
  gate
- call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or
  the network, write configuration, change defaults, write indexes, shift
  traffic, or expose source text, raw legal text, source chunks, embedding
  vectors, request bodies, response bodies, headers, prompts, raw payloads,
  model outputs, gateway responses, emails, credentials, or user identifiers
  for the Gemini embedding cheap-first preflight
- prove production model routing health
- prove route telemetry result archive rows are production health evidence,
  write configuration, call gateways, change routes, or expose raw events,
  request bodies, response bodies, headers, gateway responses, model outputs,
  emails, identifiers, or credentials for the route telemetry archive/cost
  ledger panels
- prove that route telemetry remediation suggestions have been applied, write
  configuration, call NewAPI/Gemini/gateways, or expose route prompts, request
  bodies, response bodies, headers, raw model output, emails, or credentials
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
- cheap-first and route telemetry repository, result archive, cost ledger, ops
  summary, triage, and remediation warnings remain visible in model-ops
  scenarios
