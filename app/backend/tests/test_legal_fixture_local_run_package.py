from services.legal_fixture_local_run_package import LegalFixtureLocalRunPackageService


def test_local_run_package_builds_two_serial_request_files_by_default():
    package = LegalFixtureLocalRunPackageService().build_package()

    assert package["status"] == "ready"
    assert package["summary"]["requested_fixture_limit"] == 2
    assert package["summary"]["request_file_count"] == 2
    assert package["summary"]["max_parallel_requests"] == 1
    assert len(package["request_files"]) == 2
    assert len(package["run_steps"]) == 2
    assert all(step["max_parallel_requests"] == 1 for step in package["run_steps"])
    assert all(row["endpoint_url"] == "{{APP_AI_BASE_URL}}/chat/completions" for row in package["request_files"])
    assert "sk-" not in str(package)


def test_local_run_package_contains_safe_commands_and_no_auth_headers_in_files():
    package = LegalFixtureLocalRunPackageService().build_package(1)
    request_file = package["request_files"][0]
    run_step = package["run_steps"][0]

    assert request_file["body"]["model"] == request_file["model"]
    assert "messages" in request_file["body"]
    assert "Authorization" not in str(request_file["body"])
    assert "$env:APP_AI_KEY" in run_step["command_templates"]["powershell"]
    assert "$APP_AI_KEY" in run_step["command_templates"]["curl"]
    assert "{{APP_AI_KEY}}" not in str(request_file["body"])
    assert package["environment"]["required_env"] == ["APP_AI_BASE_URL", "APP_AI_KEY"]


def test_local_run_package_includes_observation_and_report_templates():
    package = LegalFixtureLocalRunPackageService().build_package(2)
    fixture_ids = [row["fixture_id"] for row in package["request_files"]]

    assert set(package["observation_template"]) == set(fixture_ids)
    assert set(package["run_report_payload_template"]["observations"]) == set(fixture_ids)
    assert set(package["run_report_payload_template"]["run_metadata"]) == set(fixture_ids)
    assert all(
        metadata["phase"] == "cheap_first"
        for metadata in package["run_report_payload_template"]["run_metadata"].values()
    )
    assert "/api/v1/maintenance/legal-review-benchmark/fixture-smoke" in package["follow_up_endpoints"]
    assert "/api/v1/maintenance/legal-review-benchmark/fixture-run-report" in package["follow_up_endpoints"]
    assert "/api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle" in package["follow_up_endpoints"]


def test_local_run_package_clamps_fixture_limit_for_low_resource_runs():
    package = LegalFixtureLocalRunPackageService().build_package(999)

    assert package["summary"]["requested_fixture_limit"] == 4
    assert package["summary"]["request_file_count"] <= 4
    assert package["summary"]["run_step_count"] == package["summary"]["request_file_count"]


def test_local_run_package_route_returns_package():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get(
        "/api/v1/maintenance/legal-review-benchmark/local-run-package?fixture_limit=1"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["request_file_count"] == 1
    assert payload["data"]["run_steps"][0]["command_templates"]["powershell"]
