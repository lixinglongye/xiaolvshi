from services.privacy_redaction import PrivacyRedactionService


def test_privacy_redaction_detects_and_masks_sensitive_identifiers():
    text = "张三身份证号110101199003071234，手机号13800138000，邮箱zhangsan@example.com。"

    result = PrivacyRedactionService().scan(text)

    assert result["status"] == "warn"
    assert result["risk_level"] == "high"
    assert result["counts_by_type"]["chinese_resident_id"] == 1
    assert result["counts_by_type"]["mobile_phone"] == 1
    assert "[身份证号]" in result["redacted_preview"]
    assert "[手机号]" in result["redacted_preview"]
    assert "zhangsan@example.com" not in result["redacted_preview"]


def test_privacy_redaction_passes_when_no_personal_data_found():
    result = PrivacyRedactionService().scan("甲方与乙方约定服务内容、付款和违约责任。")

    assert result["status"] == "pass"
    assert result["risk_level"] == "none"
    assert result["finding_count"] == 0


def test_privacy_redaction_flags_bank_cards():
    result = PrivacyRedactionService().scan("收款账户：6222 0200 1234 5678 901。")

    assert result["status"] == "warn"
    assert result["counts_by_type"]["bank_card"] == 1
    assert "[银行卡号]" in result["redacted_preview"]
