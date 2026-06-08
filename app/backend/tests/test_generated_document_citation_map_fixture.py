import json
from pathlib import Path


def _load_mock(name: str) -> list[dict]:
    path = Path(__file__).resolve().parents[1] / "mock_data" / name
    return json.loads(path.read_text(encoding="utf-8"))


def _split_refs(value: str) -> set[str]:
    return {item.strip() for item in value.split(",") if item.strip()}


def test_generated_document_citation_map_matches_case_fact_fixture_ids():
    documents = _load_mock("generated_documents.json")
    facts = _load_mock("case_facts.json")
    materials = _load_mock("case_materials.json")

    document = next(item for item in documents if item["id"] == 1)
    case_id = document["case_id"]
    citation_map = json.loads(document["citation_map"])

    case_facts = {item["fact_no"]: item for item in facts if item["case_id"] == case_id}
    case_materials = {item["material_no"]: item for item in materials if item["case_id"] == case_id}
    referenced_fact_ids = {
        fact_id
        for fact_ids in citation_map.values()
        for fact_id in fact_ids
    }

    assert document["case_id"] == 1
    assert set(citation_map).issubset(case_materials)
    assert {"F-001", "F-002", "F-003"}.issubset(referenced_fact_ids)
    assert referenced_fact_ids.issubset(case_facts)

    for material_no, fact_ids in citation_map.items():
        material = case_materials[material_no]
        material_related_facts = _split_refs(material["related_facts"])
        assert set(fact_ids).issubset(case_facts)
        assert set(fact_ids).issubset(material_related_facts)

    audit_payload = {
        "case_id": case_id,
        "document_id": document["id"],
        "document_type": document["doc_type"],
        "material_refs": sorted(citation_map),
        "fact_refs": sorted(referenced_fact_ids),
        "document_case_consistent": all(item["case_id"] == case_id for item in case_facts.values()),
        "material_case_consistent": all(item["case_id"] == case_id for item in case_materials.values()),
    }
    audit_text = json.dumps(audit_payload, ensure_ascii=False)

    assert audit_payload["document_case_consistent"] is True
    assert audit_payload["material_case_consistent"] is True
    assert "parsed_text" not in audit_text
    assert "fact_text" not in audit_text
    assert "content" not in audit_text
