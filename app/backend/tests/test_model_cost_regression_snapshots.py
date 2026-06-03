from services.model_cost_regression_snapshots import ModelCostRegressionSnapshotService


def test_cost_regression_snapshots_pass_for_current_cheap_first_defaults():
    payload = ModelCostRegressionSnapshotService().build_snapshots()
    snapshots = {snapshot["id"]: snapshot for snapshot in payload["snapshots"]}

    assert payload["status"] == "pass"
    assert payload["summary"]["snapshot_count"] == 5
    assert payload["summary"]["failed_count"] == 0
    assert snapshots["fast-routing-5000"]["current"]["initial_model"] == "gemini-2.5-flash-lite"
    assert snapshots["classification-2500"]["current"]["initial_cost_tier"] == "lowest"
    assert snapshots["ocr-extraction-3500"]["estimated_savings_ratio"] > 0.8
    assert snapshots["pdf-premium-exception-80"]["estimated_savings_ratio"] == 0
    assert all(check["status"] == "pass" for check in payload["regression_checks"])


def test_cost_regression_snapshots_warn_when_thresholds_get_tighter():
    payload = ModelCostRegressionSnapshotService().build_snapshots(
        threshold_overrides={
            "fast-routing-5000": {
                "warn_min_savings_ratio": 0.99,
                "fail_min_savings_ratio": 0.10,
            }
        }
    )
    fast_snapshot = {snapshot["id"]: snapshot for snapshot in payload["snapshots"]}["fast-routing-5000"]

    assert payload["status"] == "warn"
    assert fast_snapshot["status"] == "warn"
    assert _check(fast_snapshot, "savings-ratio")["status"] == "warn"
    assert payload["recommended_actions"]


def test_cost_regression_snapshots_fail_when_high_volume_default_drifts_to_premium():
    payload = ModelCostRegressionSnapshotService().build_snapshots(
        model_overrides={"fast": "gemini-2.5-pro"}
    )
    fast_snapshot = {snapshot["id"]: snapshot for snapshot in payload["snapshots"]}["fast-routing-5000"]
    high_volume_check = {check["id"]: check for check in payload["regression_checks"]}[
        "high-volume-default-tier"
    ]

    assert payload["status"] == "fail"
    assert fast_snapshot["status"] == "fail"
    assert fast_snapshot["current"]["initial_cost_tier"] == "premium"
    assert _check(fast_snapshot, "initial-cost-tier")["status"] == "fail"
    assert _check(fast_snapshot, "savings-ratio")["status"] == "fail"
    assert high_volume_check["status"] == "fail"


def test_cost_regression_snapshots_report_cost_savings_against_premium_baseline():
    payload = ModelCostRegressionSnapshotService().build_snapshots()
    fast_snapshot = {snapshot["id"]: snapshot for snapshot in payload["snapshots"]}["fast-routing-5000"]

    assert fast_snapshot["cheap_first_monthly_cost_usd"] < fast_snapshot["premium_baseline_monthly_cost_usd"]
    assert fast_snapshot["estimated_savings_usd"] > 0
    assert payload["summary"]["estimated_savings_usd"] > 0
    assert payload["summary"]["premium_baseline_monthly_cost_usd"] >= payload["summary"][
        "cheap_first_monthly_cost_usd"
    ]


def test_cost_regression_snapshots_do_not_emit_sensitive_values():
    payload = ModelCostRegressionSnapshotService().build_snapshots()
    text = str(payload).lower()

    assert "sk-" not in text
    assert "api_key" not in text
    assert "password" not in text
    assert "secret" not in text
    assert "@" not in text


def test_cost_regression_snapshots_route_returns_snapshots():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/model-cost-regression-snapshots")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["snapshot_count"] == 5


def _check(snapshot, check_id):
    return {check["id"]: check for check in snapshot["checks"]}[check_id]
