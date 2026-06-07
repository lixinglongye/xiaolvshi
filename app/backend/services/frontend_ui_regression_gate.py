from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
FRONTEND_DIR = REPO_ROOT / "app" / "frontend"
PACKAGE_JSON = FRONTEND_DIR / "package.json"

COMMAND_GATES = (
    {
        "id": "frontend-lint",
        "command": "npm run lint",
        "purpose": "Reject unused UI code, unsafe imports, and stale page wiring before release.",
        "required": True,
        "script": "lint",
    },
    {
        "id": "frontend-typecheck",
        "command": "npm run typecheck",
        "purpose": "Verify React props, API response bindings, and maintenance/model-ops evidence types.",
        "required": True,
        "script": "typecheck",
    },
    {
        "id": "frontend-build",
        "command": "npm run build",
        "purpose": "Verify Vite production bundling, route imports, and prerender-safe entrypoints.",
        "required": True,
        "script": "build",
    },
    {
        "id": "frontend-ui-regression",
        "command": "npm run ui:regression",
        "purpose": "Check maintenance/model-ops UI evidence wiring, partial-load controls, and privacy-safe source contracts.",
        "required": True,
        "script": "ui:regression",
    },
)

PAGE_GATES = (
    {
        "route": "/maintenance",
        "page": "MaintenanceEvidencePage",
        "source_path": "app/frontend/src/pages/MaintenanceEvidencePage.tsx",
        "risk_area": "reviewer-facing maintenance and benchmark evidence",
        "protected_panels": (
            "partial evidence failure banner",
            "user need benchmark coverage",
            "user need Gemini route coverage",
            "legal document benchmark coverage",
            "public benchmark license gate",
            "legal benchmark fixture crosswalk",
            "legal benchmark research refresh",
            "model route legal benchmark risk queue",
            "legal RAG authority citation gate",
            "legal RAG hallucination triage gate",
            "legal RAG abstention escalation gate",
            "legal RAG retrieval diagnostics gate",
            "continuous update ledger",
            "Gemini/NewAPI selector evidence",
        ),
        "covered_by": (
            "frontend-lint",
            "frontend-typecheck",
            "frontend-build",
            "frontend-ui-regression",
            "manual-browser-smoke",
        ),
        "missing_automation": (
            "network-mocked success/failure browser regression",
        ),
    },
    {
        "route": "/model-ops",
        "page": "ModelOpsPage",
        "source_path": "app/frontend/src/pages/ModelOpsPage.tsx",
        "risk_area": "cheap-first Gemini/NewAPI operations and route telemetry",
            "protected_panels": (
                "cheap-first calibration",
                "Gemini variant matrix",
                "ModelOps load guard",
                "Performance observations",
                "Gemini catalog source audit",
                "Observed Gemini model intake queue",
                "Observed Gemini coverage gap queue",
                "Model catalog candidate patch plan",
                "Model catalog candidate impact replay",
                "Gemini/NewAPI alias capability coverage",
            "Gateway request compatibility gate",
            "Cheap-first release decision",
            "Default change queue",
            "Cheap-first priority queue",
            "Cheap-first canary plan",
            "Cheap-first canary observation review",
            "Cheap-first canary promotion decision",
            "Cheap-first canary approval packet",
            "Cheap-first canary rollback drill",
            "Cheap-first canary change manifest",
            "Cheap-first maintainer execution checklist",
            "Gemini cheap-first coverage gate",
            "Gemini cheap-first route preflight",
            "AIHub endpoint route coverage gate",
            "Gateway connection profile",
            "Cheap-first quality budget",
            "Model failure upgrade budget",
            "Legal micro benchmark preflight",
            "ModelOps legal benchmark risk bridge",
            "Cheap-first escalation budget",
            "selector replay",
            "route telemetry",
            "route telemetry repository",
            "route telemetry ops summary",
            "route telemetry triage queue",
            "route telemetry remediation",
            "gateway probe evaluation",
        ),
        "covered_by": (
            "frontend-lint",
            "frontend-typecheck",
            "frontend-build",
            "frontend-ui-regression",
            "manual-browser-smoke",
        ),
        "missing_automation": (
            "network-mocked model-ops API browser regression",
        ),
    },
    {
        "route": "/settings",
        "page": "SettingsPage",
        "source_path": "app/frontend/src/pages/SettingsPage.tsx",
        "risk_area": "user-facing feedback capture and account settings",
        "protected_panels": (
            "product feedback capture form",
            "feedback capture-plan preview",
            "feedback ticket submit action",
            "metadata-only feedback privacy boundary",
        ),
        "covered_by": (
            "frontend-lint",
            "frontend-typecheck",
            "frontend-build",
            "frontend-ui-regression",
            "manual-browser-smoke",
        ),
        "missing_automation": (
            "network-mocked feedback capture-plan and ticket-create browser regression",
        ),
    },
    {
        "route": "/deep-report/:id",
        "page": "DeepReportPage",
        "source_path": "app/frontend/src/pages/DeepReportPage.tsx",
        "risk_area": "report-level feedback capture and legal review closure",
        "protected_panels": (
            "report feedback capture form",
            "report-quality capture-plan preview",
            "report id feedback linkage",
            "metadata-only feedback privacy boundary",
        ),
        "covered_by": (
            "frontend-lint",
            "frontend-typecheck",
            "frontend-build",
            "frontend-ui-regression",
            "manual-browser-smoke",
        ),
        "missing_automation": (
            "network-mocked report feedback preview and ticket-create browser regression",
        ),
    },
)


class FrontendUiRegressionGateService:
    """Build metadata-only UI regression evidence for maintainer review."""

    def build_gate(self) -> dict[str, Any]:
        package = self._read_package_json()
        scripts = package.get("scripts") if isinstance(package.get("scripts"), dict) else {}
        command_rows = [self._command_row(gate, scripts) for gate in COMMAND_GATES]
        page_rows = [self._page_row(row, command_rows) for row in PAGE_GATES]
        missing_script_ids = [row["id"] for row in command_rows if not row["script_present"]]
        missing_automation = [
            item
            for row in page_rows
            for item in row["missing_automation"]
        ]
        required_ready = all(row["ready"] for row in command_rows if row["required"])
        status = "ready_with_gaps" if required_ready and missing_automation else ("blocked" if missing_script_ids else "ready")

        return {
            "status": status,
            "method": {
                "type": "frontend-ui-regression-gate-metadata",
                "notes": [
                    "Reads package script names and known page paths only; it does not run commands or inspect browser storage.",
                    "Tracks release gate coverage for /maintenance and /model-ops, where benchmark and cheap-first evidence is displayed.",
                    "Legal benchmark research refresh evidence is treated as metadata only: no datasets, public scores, external legal text, model calls, or credentials.",
                    "Model route legal benchmark risk queue UI evidence is metadata only: no gateway calls, routing writes, dataset downloads, raw legal text, or credentials.",
                    "Legal RAG authority citation gate UI evidence is metadata only: no NewAPI/Gemini/gateway calls, dataset downloads, raw legal text, prompts, model output, or credentials.",
                    "Legal RAG hallucination triage gate UI evidence is metadata only: no NewAPI/Gemini/gateway calls, dataset downloads, raw legal text, retrieved snippets, prompts, model output, or credentials.",
                    "Legal RAG abstention escalation gate UI evidence is metadata only: no model/gateway/network calls, dataset downloads, fixture questions, dangerous answers, raw retrieved context, raw legal text, prompts, model output, or credentials.",
                    "Legal RAG retrieval diagnostics gate UI evidence is metadata only: no model/gateway/network calls, dataset downloads, raw query, raw retrieved context, raw legal text, prompts, model output, or credentials.",
                    "ModelOps Gemini cheap-first coverage gate UI evidence is metadata only: no NewAPI/Gemini/OpenAI/Google/gateway/network calls and no raw prompts, payloads, model output, or credentials.",
                    "ModelOps Gemini cheap-first route preflight UI evidence is metadata only: no NewAPI/Gemini/OpenAI/Google/gateway/network calls, configuration writes, traffic shifts, request bodies, response bodies, headers, raw prompts, raw payloads, raw model output, legal text, emails, or credentials.",
                    "ModelOps AIHub endpoint route coverage gate UI evidence is metadata only: no NewAPI/Gemini/OpenAI/Google/gateway/app-AI/model/network calls, configuration writes, traffic shifts, request bodies, response bodies, headers, raw prompts, raw payloads, raw legal text, raw model output, emails, or credentials.",
                    "ModelOps gateway connection profile UI evidence is metadata only: no NewAPI/Gemini/OpenAI/Google/gateway/app-AI/model/network calls, configuration writes, traffic shifts, request bodies, response bodies, headers, raw prompts, raw payloads, raw legal text, raw model output, emails, credentials, or user identifiers.",
                    "ModelOps observed Gemini coverage gap queue UI evidence is metadata only: no NewAPI/Gemini/OpenAI/Google/gateway/network calls, configuration writes, traffic shifts, raw prompts, payloads, model output, legal text, emails, or credentials.",
                    "ModelOps Gemini/NewAPI alias capability coverage UI evidence is metadata only: no NewAPI/Gemini/OpenAI/Google/gateway/network calls, configuration writes, request bodies, response bodies, headers, raw prompts, payloads, model output, legal text, emails, or credentials.",
                    "ModelOps gateway request compatibility gate UI evidence is metadata only: no NewAPI/Gemini/OpenAI/Google/gateway/network calls, configuration writes, traffic shifts, headers, request bodies, prompts, raw legal text, model output, payloads, emails, or credentials.",
                    "ModelOps catalog candidate impact replay UI evidence is metadata only: no catalog/config/env writes, no NewAPI/Gemini/OpenAI/Google/gateway/network calls, and no raw prompts, payloads, model output, legal text, or credentials.",
                    "ModelOps maintainer execution checklist UI evidence is metadata only: no configuration writes, approval records, traffic shifts, gateway calls, prompts, raw model output, or credentials.",
                    "Model failure upgrade budget UI evidence is metadata only: no automatic retries, premium quota consumption, gateway calls, traffic shifts, configuration writes, prompts, raw model output, legal text, request bodies, response bodies, headers, identifiers, or credentials.",
                    "ModelOps legal micro benchmark preflight UI evidence is metadata only: no NewAPI/Gemini/OpenAI/Google calls, gateway calls, configuration writes, traffic shifts, request bodies, messages, prompt text, fixture excerpts, legal text, generated document text, model output, gateway responses, or credentials.",
                    "ModelOps legal benchmark risk bridge UI evidence is metadata only: no NewAPI/Gemini/OpenAI/Google calls, gateway calls, routing writes, dataset downloads, public benchmark scores, raw legal text, model output, prompts, or credentials.",
                    "ModelOps cheap-first escalation budget UI evidence is metadata only: no gateway calls, automatic retries, traffic shifts, raw prompts, raw model output, legal text, request bodies, response bodies, headers, identifiers, or credentials.",
                    "ModelOps route telemetry UI evidence is metadata only: repository, ops summary, triage queue, and remediation panels use sanitized route counters and never render prompts, legal text, request bodies, response bodies, headers, raw model output, emails, or credentials.",
                    "Public benchmark license gate UI evidence is metadata only: no public benchmark sample text, fixture snippets, model output, gateway payloads, dataset downloads, public score claims, or credentials.",
                    "Settings feedback capture evidence is metadata only: capture-plan previews return priority, owner, roadmap IDs, release gates, and privacy flags without raw feedback text or model calls.",
                    "Deep report feedback capture evidence is metadata only: report-level feedback links to report IDs, roadmap IDs, and release gates without raw report text, prompts, model output, or external calls.",
                    "Separates current executable gates from missing browser-level network mocking automation.",
                    "Legal benchmark fixture crosswalk UI evidence is metadata only: no public benchmark text, fixture snippets, generated text, model output, dataset downloads, or credentials.",
                ],
            },
            "summary": {
                "page_count": len(page_rows),
                "command_gate_count": len(command_rows),
                "ready_command_gate_count": sum(1 for row in command_rows if row["ready"]),
                "required_command_gate_count": sum(1 for row in command_rows if row["required"]),
                "missing_required_command_count": len(missing_script_ids),
                "protected_panel_count": sum(len(row["protected_panels"]) for row in page_rows),
                "missing_page_automation_count": len(missing_automation),
                "manual_browser_smoke_required": True,
                "model_calls": "not_required",
                "network_access": "local_only",
            },
            "command_gates": command_rows,
            "page_rows": page_rows,
            "failure_modes": [
                {
                    "id": "single-maintenance-endpoint-fails",
                    "page": "/maintenance",
                    "current_control": "Incremental maintenance task rendering and per-request timeouts keep successful evidence visible; npm run ui:regression checks the source contract.",
                    "regression_target": "Add browser-level network mocking for one API 500 and assert other evidence panels remain visible.",
                },
                {
                    "id": "cheap-first-panel-regresses",
                    "page": "/model-ops",
                    "current_control": "Typecheck/build plus npm run ui:regression verify selector, calibration, and telemetry source contracts.",
                    "regression_target": "Add browser-level mocked selector replay and assert low-cost routing warnings stay visible.",
                },
                {
                    "id": "gemini-cheap-first-coverage-gate-regresses",
                    "page": "/model-ops",
                    "current_control": "Typecheck/build plus npm run ui:regression keep the Gemini cheap-first coverage-gate panel in the ModelOps source contract.",
                    "regression_target": "Add browser-level mocked coverage-gate API checks for default, premium-exception, unknown-model, and privacy-boundary rows.",
                },
                {
                    "id": "gemini-cheap-first-route-preflight-regresses",
                    "page": "/model-ops",
                    "current_control": "Typecheck/build plus npm run ui:regression keep the Gemini cheap-first route preflight panel, endpoint binding, official-source rows, route-task rows, variant rows, checks, and privacy boundary in the ModelOps source contract.",
                    "regression_target": "Add browser-level mocked route-preflight API checks for Flash-Lite defaults, preview and premium review rows, blocked variant boundaries, source-signal summaries, and forbidden raw request/model fields.",
                },
                {
                    "id": "aihub-endpoint-route-coverage-gate-regresses",
                    "page": "/model-ops",
                    "current_control": "Typecheck/build plus npm run ui:regression keep the AIHub endpoint route coverage panel, endpoint rows, coverage matrix, checks, and privacy boundary in the ModelOps source contract.",
                    "regression_target": "Add browser-level mocked AIHub route-coverage API checks for runtime-router flags, route telemetry gaps, legacy media route gaps, response payload boundaries, and forbidden raw request/model fields.",
                },
                {
                    "id": "user-need-gemini-route-coverage-regresses",
                    "page": "/maintenance",
                    "current_control": "Typecheck/build plus npm run ui:regression keep the user need Gemini route coverage panel, endpoint binding, linked route tasks, default models, official-source URLs, claim boundary, and privacy boundary in the maintenance source contract.",
                    "regression_target": "Add browser-level mocked route-coverage API checks for Flash-Lite protected needs, premium review rows, unmapped route blockers, no default route changes, and forbidden raw route payload fields.",
                },
                {
                    "id": "gemini-alias-capability-coverage-regresses",
                    "page": "/model-ops",
                    "current_control": "Typecheck/build plus npm run ui:regression keep the Gemini/NewAPI alias capability coverage panel in the ModelOps source contract.",
                    "regression_target": "Add browser-level mocked alias-capability API checks for yibu/NewAPI/action-suffix aliases, unknown models, external models, and privacy-boundary rows.",
                },
                {
                    "id": "gateway-request-compatibility-gate-regresses",
                    "page": "/model-ops",
                    "current_control": "Typecheck/build plus npm run ui:regression keep the gateway request compatibility gate panel, API binding, and privacy boundary in the ModelOps source contract.",
                    "regression_target": "Add browser-level mocked gateway-request-compatibility API checks for task defaults, JSON response shapes, reasoning policy omissions, unsafe overrides, unknown models, and forbidden raw request fields.",
                },
                {
                    "id": "cheap-first-escalation-budget-regresses",
                    "page": "/model-ops",
                    "current_control": "Typecheck/build plus npm run ui:regression keep the cheap-first escalation budget panel, aggregate payload guard, and privacy boundary in the ModelOps source contract.",
                    "regression_target": "Add browser-level mocked escalation-budget API checks for runaway retries, wasted escalation spend, premium review coverage, and forbidden raw fields.",
                },
                {
                    "id": "route-telemetry-ui-contract-regresses",
                    "page": "/model-ops",
                    "current_control": "Typecheck/build plus npm run ui:regression keep route telemetry repository, ops summary, triage queue, remediation plan, ordering, and privacy boundaries in the ModelOps source contract.",
                    "regression_target": "Add browser-level mocked route telemetry API checks for empty repositories, warning triage rows, remediation env suggestions, no config writes, no gateway calls, and forbidden raw request/model fields.",
                },
                {
                    "id": "model-failure-upgrade-budget-regresses",
                    "page": "/model-ops",
                    "current_control": "Typecheck/build plus npm run ui:regression keep the model failure upgrade budget panel, sanitized payload guard, and privacy boundary in the ModelOps source contract.",
                    "regression_target": "Add browser-level mocked failure-upgrade-budget API checks for retry-up decisions, premium approval blocks, attempt exhaustion, hard-stop signals, and forbidden raw fields.",
                },
                {
                    "id": "modelops-legal-micro-benchmark-preflight-regresses",
                    "page": "/model-ops",
                    "current_control": "Typecheck/build plus npm run ui:regression keep the legal micro benchmark preflight panel, endpoint binding, serial run cap, and metadata-only privacy boundary in the ModelOps source contract.",
                    "regression_target": "Add browser-level mocked legal-micro-benchmark-preflight API checks for fixture rows, document rows, fact rows, run sequence, no gateway calls, and no raw legal/model/payload fields.",
                },
                {
                    "id": "modelops-legal-benchmark-risk-bridge-regresses",
                    "page": "/model-ops",
                    "current_control": "Typecheck/build plus npm run ui:regression keep the legal benchmark risk bridge panel, policy boundary, and privacy boundary in the ModelOps source contract.",
                    "regression_target": "Add browser-level mocked legal-benchmark-risk-bridge API checks for route watchlists, user-need gaps, premium exception rows, and no raw legal/benchmark/model fields.",
                },
                {
                    "id": "public-benchmark-license-gate-regresses",
                    "page": "/maintenance",
                    "current_control": "Typecheck/build plus npm run ui:regression keep the public benchmark license gate panel, review checklist, and claim/privacy boundary in the maintenance source contract.",
                    "regression_target": "Add browser-level mocked public-license-gate API checks for blocked sources, reviewed metadata-only sources, user-need mappings, route-risk mappings, and forbidden raw benchmark/model/gateway fields.",
                },
                {
                    "id": "raw-private-output-renders",
                    "page": "/maintenance",
                    "current_control": "Backend services emit metadata-only benchmark evidence and npm run ui:regression scans UI sources for forbidden sensitive examples.",
                    "regression_target": "Add rendered DOM assertions that fixture snippets, raw model output, credentials, and user feedback text are absent.",
                },
                {
                    "id": "feedback-capture-plan-regresses",
                    "page": "/settings",
                    "current_control": "Typecheck/build plus npm run ui:regression keep the product feedback form, capture-plan API binding, ticket creation path, and privacy-boundary rendering in the source contract.",
                    "regression_target": "Add browser-level mocked capture-plan 200/500 checks and assert raw user feedback text is not rendered in the preview summary.",
                },
                {
                    "id": "deep-report-feedback-capture-regresses",
                    "page": "/deep-report/:id",
                    "current_control": "Typecheck/build plus npm run ui:regression keep the report-level feedback panel bound to report_quality and report identifiers.",
                    "regression_target": "Add browser-level mocked report feedback submission checks and assert report body text is not sent to capture-plan previews.",
                },
            ],
            "recommended_actions": self._recommended_actions(missing_script_ids, missing_automation),
            "privacy_boundary": {
                "reads_package_script_names": True,
                "reads_page_source_paths": True,
                "returns_source_code": False,
                "returns_raw_browser_storage": False,
                "returns_raw_prompts": False,
                "returns_raw_payloads": False,
                "returns_raw_query": False,
                "returns_raw_retrieved_context": False,
                "returns_raw_model_output": False,
                "returns_external_legal_text": False,
                "downloads_benchmark_datasets": False,
                "calls_models": False,
                "calls_newapi": False,
                "calls_gemini": False,
                "calls_openai": False,
                "calls_google": False,
                "calls_gateways": False,
                "calls_network": False,
                "writes_model_routes": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
            },
            "validation_commands": [
                "npm run lint",
                "npm run typecheck",
                "npm run build",
                "npm run ui:regression",
                "python -m pytest tests/test_frontend_ui_regression_gate.py tests/test_release_readiness.py -q",
            ],
        }

    def _read_package_json(self) -> dict[str, Any]:
        if not PACKAGE_JSON.exists():
            return {}
        try:
            parsed = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _command_row(self, gate: dict[str, Any], scripts: dict[str, Any]) -> dict[str, Any]:
        script_name = str(gate["script"])
        script_present = script_name in scripts and isinstance(scripts.get(script_name), str)
        return {
            "id": gate["id"],
            "command": gate["command"],
            "purpose": gate["purpose"],
            "required": bool(gate["required"]),
            "script_present": script_present,
            "ready": script_present,
            "gap_reason": "" if script_present else f"missing_package_script:{script_name}",
        }

    def _page_row(self, row: dict[str, Any], command_rows: list[dict[str, Any]]) -> dict[str, Any]:
        source_path = str(row["source_path"])
        source_exists = (REPO_ROOT / source_path).exists()
        ready_gate_ids = {gate["id"] for gate in command_rows if gate["ready"]}
        covered_by = [str(item) for item in row["covered_by"]]
        ready_cover = [gate_id for gate_id in covered_by if gate_id == "manual-browser-smoke" or gate_id in ready_gate_ids]
        missing_cover = [gate_id for gate_id in covered_by if gate_id not in ready_cover]
        return {
            "route": row["route"],
            "page": row["page"],
            "source_path": source_path,
            "source_exists": source_exists,
            "risk_area": row["risk_area"],
            "protected_panels": list(row["protected_panels"]),
            "covered_by": covered_by,
            "ready_cover": ready_cover,
            "missing_cover": missing_cover,
            "missing_automation": list(row["missing_automation"]),
            "status": "ready_with_gaps" if source_exists and not missing_cover else "blocked",
        }

    def _recommended_actions(self, missing_script_ids: list[str], missing_automation: list[str]) -> list[str]:
        if missing_script_ids:
            return [
                "Restore missing frontend package scripts before treating UI evidence as release-ready: "
                + ", ".join(missing_script_ids)
                + ".",
                "Run lint, typecheck, and build after every maintenance or model-ops UI change.",
            ]
        actions = [
            "Keep npm run lint, npm run typecheck, npm run build, and npm run ui:regression in the frontend release gate.",
            "Add browser-level network mocking for /maintenance and /model-ops success, one-endpoint failure, and privacy-safe rendering.",
        ]
        if missing_automation:
            actions.append("Prioritize the missing UI automation targets before making broad public readiness claims.")
        return actions
