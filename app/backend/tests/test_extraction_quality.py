from services.extraction_quality import ExtractionQualityAuditService


def test_extraction_quality_passes_dense_text_layer():
    result = ExtractionQualityAuditService().evaluate(
        {
            "char_count": 12_000,
            "page_count": 10,
            "text_layer_pages": list(range(1, 11)),
            "low_text_pages": [],
            "ocr_pages": [],
            "warnings": [],
        }
    )

    assert result["status"] == "pass"
    assert result["score"] >= 90
    assert result["chars_per_page"] == 1200


def test_extraction_quality_fails_too_little_text():
    result = ExtractionQualityAuditService().evaluate({"char_count": 80, "page_count": 4})

    assert result["status"] == "fail"
    assert result["blocking_reasons"]
    assert result["score"] <= 55


def test_extraction_quality_warns_on_scanned_or_weak_text_pages():
    result = ExtractionQualityAuditService().evaluate(
        {
            "char_count": 1800,
            "page_count": 12,
            "text_layer_pages": [],
            "low_text_pages": [1, 2, 3, 4, 5],
            "ocr_pages": [1, 2, 3, 4, 5, 6],
            "warnings": ["第 7 页 OCR 未识别到有效文本。"],
        }
    )

    assert result["status"] == "warn"
    assert result["ocr_page_count"] == 6
    assert any("OCR" in item for item in result["warning_reasons"])
