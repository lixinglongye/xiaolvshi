import json
from datetime import date

from services.legal_knowledge_audit import LegalKnowledgeAuditService


def _record(source_id: str, topics: list[str] | None = None) -> dict:
    return {
        "source_id": source_id,
        "source_name": "《中华人民共和国民法典》",
        "article_number": "第一条",
        "article_title": "测试条文",
        "source_type": "法律",
        "authority_level": "裁判依据",
        "jurisdiction": "中国大陆",
        "legal_domain": "合同审查",
        "topics": topics or ["合同效力"],
        "keywords": ["合同"],
        "text": "测试文本",
        "summary": "测试摘要",
        "source_url": "https://example.com/source.pdf",
        "official_source_url": "https://example.com/",
        "effective_status": "现行有效",
        "verification_status": "已校验",
    }


def _write_seed(tmp_path, payload: dict):
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_legal_knowledge_audit_passes_complete_recent_seed(tmp_path):
    topics = ["合同效力", "主体资格", "格式条款", "违约责任", "解除", "损害赔偿", "担保", "租赁"]
    seed = {
        "schema_version": "1.0",
        "generated_at": "2026-05-14",
        "records": [_record(f"CIVIL-{index}", [topic]) for index, topic in enumerate(topics, start=1)],
    }

    result = LegalKnowledgeAuditService().audit_seed_file(_write_seed(tmp_path, seed), today=date(2026, 6, 3))

    assert result["status"] == "pass"
    assert result["record_count"] == len(topics)
    assert result["duplicate_source_ids"] == []
    assert result["missing_critical_topics"] == []


def test_legal_knowledge_audit_fails_duplicate_or_missing_required_fields(tmp_path):
    bad_record = _record("CIVIL-1")
    bad_record["summary"] = ""
    seed = {
        "schema_version": "1.0",
        "generated_at": "2026-05-14",
        "records": [_record("CIVIL-1"), bad_record],
    }

    result = LegalKnowledgeAuditService().audit_seed_file(_write_seed(tmp_path, seed), today=date(2026, 6, 3))

    assert result["status"] == "fail"
    assert result["duplicate_source_ids"] == ["CIVIL-1"]
    assert result["missing_required_fields"][0]["fields"] == ["summary"]


def test_legal_knowledge_audit_warns_on_stale_or_missing_topic_coverage(tmp_path):
    seed = {
        "schema_version": "1.0",
        "generated_at": "2025-01-01",
        "records": [_record("CIVIL-1", ["合同效力"])],
    }

    result = LegalKnowledgeAuditService().audit_seed_file(_write_seed(tmp_path, seed), today=date(2026, 6, 3))

    assert result["status"] == "warn"
    assert result["age_days"] > result["max_age_days"]
    assert "担保" in result["missing_critical_topics"]
