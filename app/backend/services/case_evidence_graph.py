from __future__ import annotations

from typing import Any


class CaseEvidenceGraphService:
    """Build a deterministic fact-evidence-citation-risk graph summary."""

    def build_graph(self, report: dict[str, Any] | None = None) -> dict[str, Any]:
        report = report if isinstance(report, dict) else {}
        risk_items = _dicts(report.get("risk_items"))
        pending_facts = _list(report.get("pending_facts"))
        appendix = _dicts(report.get("legal_authority_appendix"))
        framework = report.get("professional_review_framework")
        framework = framework if isinstance(framework, dict) else {}

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        appendix_ids = {_source_id(source, index) for index, source in enumerate(appendix)}

        for index, risk in enumerate(risk_items):
            risk_id = _risk_id(risk, index)
            nodes.append(
                {
                    "id": f"risk:{risk_id}",
                    "type": "risk",
                    "label": _text(risk.get("title")) or risk_id,
                    "risk_level": _risk_level(risk.get("risk_level")),
                    "review_state": "needs_evidence_graph_review",
                }
            )
            for evidence_index, suggestion in enumerate(_evidence_suggestions(risk), start=1):
                evidence_id = f"evidence:{risk_id}:{evidence_index:02d}"
                nodes.append(
                    {
                        "id": evidence_id,
                        "type": "evidence_requirement",
                        "label": suggestion,
                        "source": "risk.evidence_suggestion",
                    }
                )
                edges.append(
                    {
                        "id": f"{evidence_id}->risk:{risk_id}",
                        "from": evidence_id,
                        "to": f"risk:{risk_id}",
                        "type": "supports_risk_review",
                    }
                )
            for citation_index, citation in enumerate(_dicts(risk.get("citations")), start=1):
                source_id = _text(citation.get("source_id")) or f"{risk_id}-citation-{citation_index}"
                citation_node_id = f"citation:{source_id}"
                nodes.append(
                    {
                        "id": citation_node_id,
                        "type": "citation",
                        "label": _text(citation.get("source_name")) or source_id,
                        "source_id": source_id,
                        "appendix_linked": source_id in appendix_ids,
                    }
                )
                edges.append(
                    {
                        "id": f"{citation_node_id}->risk:{risk_id}",
                        "from": citation_node_id,
                        "to": f"risk:{risk_id}",
                        "type": "cites_authority_for",
                    }
                )

        for index, fact in enumerate(pending_facts, start=1):
            fact_id = f"PF-{index:03d}"
            fact_label = _pending_fact_label(fact, index)
            nodes.append(
                {
                    "id": f"fact:{fact_id}",
                    "type": "pending_fact",
                    "label": fact_label,
                    "blocking": _is_blocking_fact(fact),
                }
            )
            for risk_index, risk in enumerate(risk_items):
                risk_id = _risk_id(risk, risk_index)
                if _risk_level(risk.get("risk_level")) in {"critical", "high"}:
                    edges.append(
                        {
                            "id": f"fact:{fact_id}->risk:{risk_id}",
                            "from": f"fact:{fact_id}",
                            "to": f"risk:{risk_id}",
                            "type": "blocks_high_risk_review",
                        }
                    )

        for index, item in enumerate(_list_text(framework.get("evidence_checklist")), start=1):
            nodes.append(
                {
                    "id": f"checklist:{index:02d}",
                    "type": "evidence_checklist_item",
                    "label": item,
                    "source": "professional_review_framework.evidence_checklist",
                }
            )

        nodes = _dedupe_nodes(nodes)
        gap_flags = self._gap_flags(nodes, edges, risk_items)
        status = self._status(risk_items, gap_flags)
        return {
            "status": status,
            "method": {
                "type": "case-evidence-graph-policy",
                "notes": [
                    "Builds a graph summary from already-normalized report fields only.",
                    "Does not query databases, call models, or read uploaded client files.",
                    "Use this as a backend contract before building a full evidence graph UI.",
                ],
            },
            "summary": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "risk_count": sum(1 for node in nodes if node["type"] == "risk"),
                "evidence_requirement_count": sum(1 for node in nodes if node["type"] == "evidence_requirement"),
                "citation_count": sum(1 for node in nodes if node["type"] == "citation"),
                "pending_fact_count": sum(1 for node in nodes if node["type"] == "pending_fact"),
                "blocking_gap_count": sum(1 for flag in gap_flags if flag["severity"] == "blocking"),
                "warning_gap_count": sum(1 for flag in gap_flags if flag["severity"] == "warning"),
            },
            "nodes": nodes,
            "edges": edges,
            "gap_flags": gap_flags,
            "delivery_phases": [
                {
                    "id": "graph-contract",
                    "title": "Backend graph contract",
                    "exit_criteria": [
                        "Risk, evidence, citation, and pending-fact nodes are stable.",
                        "Blocking gaps are explicit before frontend implementation.",
                    ],
                },
                {
                    "id": "case-workbench-ui",
                    "title": "Case workbench graph UI",
                    "exit_criteria": [
                        "Reviewers can filter risks by missing evidence and citation support.",
                        "Pending facts link back to affected high-risk findings.",
                    ],
                },
            ],
            "validation_commands": [
                "python -m pytest tests/test_case_evidence_graph.py -q",
                "python -m pytest tests/test_evidence_audit.py tests/test_citation_audit.py -q",
            ],
            "privacy_note": (
                "Privacy policy: graph nodes should use normalized labels, IDs, statuses, and counts. Do not store raw client "
                "documents, full model outputs, emails, credentials, or private case narratives in graph evidence."
            ),
        }

    def _gap_flags(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        risk_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        flags: list[dict[str, Any]] = []
        if not risk_items:
            return [
                {
                    "id": "no-risk-items",
                    "severity": "warning",
                    "target": "risk_items",
                    "message": "No risk items are available to build a case evidence graph.",
                }
            ]

        edge_targets = {
            edge["to"]
            for edge in edges
            if edge["type"] in {"supports_risk_review", "cites_authority_for"}
        }
        citation_targets = {edge["to"] for edge in edges if edge["type"] == "cites_authority_for"}
        for index, risk in enumerate(risk_items):
            risk_id = _risk_id(risk, index)
            target = f"risk:{risk_id}"
            level = _risk_level(risk.get("risk_level"))
            if target not in edge_targets:
                flags.append(
                    {
                        "id": f"{risk_id}-no-supporting-edge",
                        "severity": "blocking" if level in {"critical", "high"} else "warning",
                        "target": target,
                        "message": "Risk has no evidence or citation edges.",
                    }
                )
            if level in {"critical", "high"} and target not in citation_targets:
                flags.append(
                    {
                        "id": f"{risk_id}-missing-reviewable-citation-edge",
                        "severity": "blocking",
                        "target": target,
                        "message": "High-risk item is missing a citation edge.",
                    }
                )

        for node in nodes:
            if node["type"] == "citation" and not node.get("appendix_linked"):
                flags.append(
                    {
                        "id": f"{node['source_id']}-missing-appendix-source",
                        "severity": "warning",
                        "target": node["id"],
                        "message": "Citation node is not linked to the legal authority appendix.",
                    }
                )
            if node["type"] == "pending_fact" and node.get("blocking"):
                flags.append(
                    {
                        "id": f"{node['id']}-blocking-pending-fact",
                        "severity": "blocking",
                        "target": node["id"],
                        "message": "Blocking pending fact must be resolved before relying on high-risk conclusions.",
                    }
                )
        return flags

    def _status(self, risk_items: list[dict[str, Any]], gap_flags: list[dict[str, Any]]) -> str:
        if not risk_items:
            return "template"
        if any(flag["severity"] == "blocking" for flag in gap_flags):
            return "blocked"
        if gap_flags:
            return "review_recommended"
        return "ready"


def _evidence_suggestions(risk: dict[str, Any]) -> list[str]:
    analysis = risk.get("legal_analysis") if isinstance(risk.get("legal_analysis"), dict) else {}
    values = _list_text(analysis.get("evidence_suggestion"))
    values.extend(_list_text(risk.get("evidence_suggestions")))
    return _dedupe_text(values)


def _pending_fact_label(value: Any, index: int) -> str:
    if isinstance(value, dict):
        return _text(value.get("field")) or _text(value.get("name")) or f"pending fact {index}"
    return _text(value) or f"pending fact {index}"


def _is_blocking_fact(value: Any) -> bool:
    if isinstance(value, dict):
        blob = "\n".join(_text(value.get(key)) for key in ("field", "name", "reason", "impact"))
    else:
        blob = _text(value)
    text = blob.lower()
    return any(marker in text for marker in ("critical", "material", "must", "required", "unable to judge"))


def _source_id(item: dict[str, Any], index: int) -> str:
    return _text(item.get("source_id")) or f"source-{index + 1}"


def _risk_id(item: dict[str, Any], index: int) -> str:
    return _text(item.get("risk_id")) or _text(item.get("risk_no")) or f"R-{index + 1:03d}"


def _risk_level(value: Any) -> str:
    raw = _text(value).lower()
    if raw in {"critical", "major", "severe"}:
        return "critical"
    if raw == "high":
        return "high"
    if raw == "low":
        return "low"
    return "medium"


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for node in nodes:
        if node["id"] in seen:
            continue
        seen.add(node["id"])
        result.append(node)
    return result


def _dedupe_text(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = "".join(value.lower().split())
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in _list(value) if isinstance(item, dict)]


def _list_text(value: Any) -> list[str]:
    return [_text(item) for item in _list(value) if _text(item)]
