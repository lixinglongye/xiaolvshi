from routers.admin_ops import _with_feedback_capture_summary
from services.feedback_capture_plan import FeedbackCapturePlanService


def test_admin_feedback_capture_summary_adds_small_derived_fields_without_raw_echo():
    raw_content = "The generated report has an incorrect citation and hallucination."
    row = {
        "id": 101,
        "category": "report_quality",
        "content": raw_content,
        "status": "open",
        "resolution_note": "",
    }

    summarized = _with_feedback_capture_summary(row, FeedbackCapturePlanService())
    summary_text = str(
        {
            "capture_summary": summarized["capture_summary"],
            "roadmap_summary": summarized["roadmap_summary"],
            "lifecycle_summary": summarized["lifecycle_summary"],
        }
    )

    assert summarized["capture_summary"]["linked_need_id"] == "traceable-legal-review"
    assert summarized["roadmap_summary"] == {
        "status": "aligned",
        "top_need_id": "traceable-legal-review",
        "match_count": 1,
    }
    assert summarized["lifecycle_summary"]["state"] == "triage"
    assert summarized["lifecycle_summary"]["blocking_check_ids"] == []
    assert "citation_audit" in summarized["capture_summary"]["release_gate_links"]
    assert raw_content not in summary_text


def test_admin_feedback_capture_summary_limits_list_fields():
    row = {
        "id": 102,
        "category": "report_quality",
        "content": "The answer hallucination has incorrect citation and missed risk.",
        "status": "open",
    }

    summarized = _with_feedback_capture_summary(row, FeedbackCapturePlanService())

    assert len(summarized["capture_summary"]["release_gate_links"]) <= 5
    assert len(summarized["capture_summary"]["missing_required_fields"]) <= 5
    assert len(summarized["lifecycle_summary"]["blocking_check_ids"]) <= 5
    assert len(summarized["lifecycle_summary"]["required_actions"]) <= 3
    assert all(len(action) <= 160 for action in summarized["lifecycle_summary"]["required_actions"])


def test_admin_feedback_capture_summary_maps_legacy_status_to_lifecycle_state():
    row = {
        "id": 103,
        "category": "report_quality",
        "content": "The report fix is ready for validation.",
        "status": "processing",
        "assignee": "legal_quality_owner",
    }

    summarized = _with_feedback_capture_summary(row, FeedbackCapturePlanService())

    assert summarized["lifecycle_summary"]["state"] == "in_progress"
    assert summarized["lifecycle_summary"]["next_state"] == "release_validation"
