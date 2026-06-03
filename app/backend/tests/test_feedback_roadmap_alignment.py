from services.feedback_roadmap_alignment import FeedbackRoadmapAlignmentService


def test_feedback_roadmap_aligns_legal_quality_to_traceable_review():
    result = FeedbackRoadmapAlignmentService().align(
        category="bug",
        content="The report has an incorrect citation and hallucination in the legal advice.",
    )

    assert result["status"] == "aligned"
    assert result["top_need_id"] == "traceable-legal-review"
    assert result["triage"]["priority"] == "P1"
    assert result["matches"][0]["confidence"] >= 70
    assert "release_decision" in result["matches"][0]["release_gate_links"]


def test_feedback_roadmap_aligns_privacy_feedback_to_safe_upload():
    result = FeedbackRoadmapAlignmentService().align(
        category="security",
        content="用户反馈上传文件里有个人信息和隐私泄露风险。",
    )

    assert result["top_need_id"] == "privacy-safe-upload"
    assert result["triage"]["priority"] == "P0"
    assert "privacy_redaction" in result["matches"][0]["release_gate_links"]


def test_feedback_roadmap_aligns_ocr_and_upload_failures_to_extraction_quality():
    result = FeedbackRoadmapAlignmentService().align(
        category="bug",
        content="PDF 上传后 OCR 识别失败，解析出来是空白。",
    )

    assert result["top_need_id"] == "robust-extraction-quality"
    assert result["triage"]["priority"] == "P2"
    assert "extraction_quality" in result["matches"][0]["release_gate_links"]


def test_feedback_roadmap_aligns_model_cost_feedback_to_cheap_first_routing():
    result = FeedbackRoadmapAlignmentService().align(
        category="suggestion",
        content="Gemini premium model is too expensive and slow; please use cheaper models first.",
    )

    assert result["top_need_id"] == "cheap-first-review-routing"
    assert "model_ops" == result["matches"][0]["category"]
    assert "model_budget" in result["matches"][0]["release_gate_links"]


def test_feedback_roadmap_catalog_exposes_mapping_coverage():
    catalog = FeedbackRoadmapAlignmentService().build_mapping_catalog()

    assert catalog["status"] == "ready"
    assert catalog["rule_count"] >= 6
    assert "feedback-to-roadmap-loop" in catalog["mapped_need_ids"]
    assert "sk-" not in str(catalog)


def test_feedback_roadmap_route_returns_catalog():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/feedback-roadmap")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"
