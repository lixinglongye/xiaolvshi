from services.model_usage import ModelUsageRegistry


def test_model_usage_registry_aggregates_by_model_and_task():
    registry = ModelUsageRegistry()

    registry.record(
        model="gemini-2.5-flash-lite",
        task="ocr",
        success=True,
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        latency_ms=120,
    )
    registry.record(
        model="gemini-2.5-flash-lite",
        task="classification",
        success=False,
        usage=None,
        latency_ms=80,
    )

    snapshot = registry.snapshot()
    model_snapshot = snapshot["models"]["gemini-2.5-flash-lite"]

    assert snapshot["totals"]["requests"] == 2
    assert snapshot["totals"]["successes"] == 1
    assert snapshot["totals"]["failures"] == 1
    assert snapshot["totals"]["total_tokens"] == 15
    assert model_snapshot["tasks"] == {"classification": 1, "ocr": 1}
    assert model_snapshot["avg_latency_ms"] == 100


def test_model_usage_registry_reset_clears_counters():
    registry = ModelUsageRegistry()
    registry.record(model="m", task="text", success=True)

    registry.reset()

    assert registry.snapshot() == {
        "totals": {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
        "models": {},
    }
