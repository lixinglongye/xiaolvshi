import re

from services.continuous_update_ledger import (
    TARGET_CONTINUOUS_HOURS,
    TARGET_MEDIUM_LARGE_UPDATE_COUNT,
    ContinuousUpdateLedgerService,
)
from services.release_readiness import ReleaseReadinessService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def test_continuous_update_ledger_tracks_goal_without_claiming_completion():
    ledger = ContinuousUpdateLedgerService().build_ledger()

    assert ledger["status"] == "in_progress"
    assert ledger["goal"]["target_continuous_hours"] == TARGET_CONTINUOUS_HOURS
    assert ledger["goal"]["target_medium_large_update_count"] == TARGET_MEDIUM_LARGE_UPDATE_COUNT
    assert ledger["summary"]["completed_medium_large_update_count"] >= 10
    assert ledger["summary"]["completed_medium_large_update_count"] < TARGET_MEDIUM_LARGE_UPDATE_COUNT
    assert ledger["summary"]["remaining_medium_large_update_count"] > 0
    assert ledger["summary"]["continuous_hours_verified"] == 0
    assert ledger["summary"]["completion_ready"] is False
    assert not SECRET_PATTERN.search(str(ledger))


def test_continuous_update_ledger_completed_entries_are_reviewable():
    ledger = ContinuousUpdateLedgerService().build_ledger()
    completed = ledger["completed_updates"]
    categories = ledger["summary"]["category_counts"]

    assert completed
    assert categories["benchmark"] >= 5
    assert categories["model_ops"] >= 3
    assert categories["frontend_ui"] >= 2
    assert all(entry["size"] in {"medium", "large"} for entry in completed)
    assert all(entry["status"] == "shipped" for entry in completed)
    assert all(entry["evidence_paths"] for entry in completed)
    assert all(entry["release_gate_links"] for entry in completed)


def test_continuous_update_ledger_prioritizes_low_resource_next_work():
    ledger = ContinuousUpdateLedgerService().build_ledger()
    queue_ids = {entry["id"] for entry in ledger["next_update_queue"]}

    assert "cheap-first-result-archive" in queue_ids
    assert "gemini-price-refresh-monitor" in queue_ids
    assert "small-legal-document-corpus-expansion" in queue_ids
    assert "frontend-local-run-review-form" in queue_ids
    assert ledger["low_resource_test_policy"]["max_parallel_requests"] == 1
    assert ledger["low_resource_test_policy"]["network_access"] == "disabled_by_default"


def test_continuous_update_ledger_is_optional_release_evidence():
    service = ReleaseReadinessService()
    ledger_commands = [
        item for item in service.default_validation_commands() if item["check_id"] == "continuous-update-ledger"
    ]
    result = service.evaluate({"continuous-update-ledger": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "continuous-update-ledger")

    assert ledger_commands == [
        {
            "check_id": "continuous-update-ledger",
            "command": "python -m pytest tests/test_continuous_update_ledger.py -q",
        }
    ]
    assert check["required"] is False
    assert check["blocks_release"] is False


def test_continuous_update_ledger_route_returns_progress_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/continuous-update-ledger")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "in_progress"
    assert payload["data"]["summary"]["completion_ready"] is False
