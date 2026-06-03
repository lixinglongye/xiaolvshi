from __future__ import annotations

import importlib


EXPECTED_RUNTIME_OPENAPI_PATHS = {
    "/api/v1/cases/{case_id}/workbench/state",
    "/api/v1/legal-rag/retrieval-plan",
    "/api/v1/billing-usage/me",
}


def test_main_router_discovery_exposes_runtime_paths_in_openapi(monkeypatch):
    monkeypatch.setenv("IS_LAMBDA", "true")

    main = importlib.import_module("main")

    openapi_paths = set(main.app.openapi().get("paths", {}))

    assert EXPECTED_RUNTIME_OPENAPI_PATHS <= openapi_paths
