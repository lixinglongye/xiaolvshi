from services.document_preflight import DocumentReviewPreflightService


def test_document_preflight_routes_simple_contract_to_cheap_first():
    text = "甲方与乙方签订服务协议，约定服务内容、费用、付款、违约责任和争议解决。"

    result = DocumentReviewPreflightService().evaluate(
        document_text=text,
        document_type="服务合同",
        user_role="甲方",
        known_facts=["签署前审查"],
    )

    assert result["status"] in {"ready", "needs_context"}
    assert result["strategy"]["strategy_id"] == "service_contract"
    assert result["routing"]["recommended_task"] == "fast"
    assert result["routing"]["budget_mode"] == "cheap-first"


def test_document_preflight_blocks_empty_or_non_legal_short_text():
    result = DocumentReviewPreflightService().evaluate(document_text="今日天气很好。")

    assert result["status"] == "blocked"
    assert result["blocking_reasons"]


def test_document_preflight_escalates_complex_financing_dispute():
    text = (
        "甲方乙方签订股权投资协议，涉及对赌、回购、担保、质押、融资、仲裁和保全。"
        "违约责任、争议解决、付款、交割和股东权利均需审查。"
    ) * 300

    result = DocumentReviewPreflightService().evaluate(
        document_text=text,
        document_type="股权投资协议",
        user_role="投资方",
        extraction={"page_count": 90},
    )

    assert result["document_signals"]["complexity_level"] == "complex"
    assert result["routing"]["recommended_task"] == "pdf"
    assert "premium" in result["routing"]["cost_tier"]
    assert result["warning_reasons"]


def test_document_preflight_warns_on_missing_strategy_facts():
    text = "甲方与乙方签订租赁合同，约定租金和押金，但未写明维修和交付验收安排。"

    result = DocumentReviewPreflightService().evaluate(
        document_text=text,
        document_type="租赁合同",
        user_role="承租方",
    )

    assert result["status"] == "needs_context"
    assert result["missing_required_facts"]
    assert any("missing facts" in action or "补充" in action for action in result["recommended_actions"])
