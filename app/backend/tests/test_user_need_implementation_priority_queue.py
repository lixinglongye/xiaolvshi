import re

from services.user_need_implementation_priority_queue import UserNeedImplementationPriorityQueueService


def test_user_need_implementation_priority_queue_prioritizes_local_gaps_and_reviews():
    queue = UserNeedImplementationPriorityQueueService().build_queue()

    assert queue["status"] == "blocked"
    assert queue["summary"]["queue_item_count"] >= 7
    assert queue["summary"]["blocked_action_count"] >= 1
    assert queue["summary"]["review_required_action_count"] >= 1
    assert queue["summary"]["public_benchmark_review_item_count"] >= 1
    assert queue["summary"]["calibration_attention_item_count"] == 0
    assert queue["summary"]["local_run_only"] is True
    assert queue["summary"]["external_dataset_downloads"] is False

    scores = [item["queue_priority_score"] for item in queue["queue_items"]]
    assert scores == sorted(scores, reverse=True)
    rows = {item["need_id"]: item for item in queue["queue_items"]}
    assert rows["traceable-legal-review"]["action_status"] == "review_required"
    assert "public-benchmark-license-review" in rows["traceable-legal-review"]["implementation_tracks"]
    assert rows["feedback-to-roadmap-loop"]["action_status"] == "blocked"
    assert "missing-local-benchmark-coverage" in rows["feedback-to-roadmap-loop"]["blocker_codes"]
    assert "local-benchmark-fixture" in rows["feedback-to-roadmap-loop"]["implementation_tracks"]


def test_user_need_implementation_priority_queue_keeps_privacy_boundary_metadata_only():
    queue = UserNeedImplementationPriorityQueueService().build_queue()
    serialized = str(queue).lower()

    assert queue["privacy_boundary"]["returns_raw_benchmark_samples"] is False
    assert queue["privacy_boundary"]["returns_public_benchmark_text"] is False
    assert queue["privacy_boundary"]["returns_fixture_snippets"] is False
    assert queue["privacy_boundary"]["returns_calibration_payloads"] is False
    assert queue["privacy_boundary"]["model_calls"] is False
    assert queue["privacy_boundary"]["network_access"] is False
    assert queue["source_boundary"]["imports_public_benchmark_samples"] is False
    assert "service agreement. alpha service provider" not in serialized
    assert "borrower id number" not in serialized
    assert re.search(r"\bsk-[A-Za-z0-9]{20,}\b", serialized) is None
    assert "@" not in serialized


def test_user_need_implementation_priority_queue_route_returns_queue():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/user-needs/implementation-priority-queue")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["queue_item_count"] >= 7
    assert payload["data"]["summary"]["model_calls"] == "not_required"
