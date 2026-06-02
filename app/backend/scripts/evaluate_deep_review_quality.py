from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.deep_review import DeepReviewService  # noqa: E402


def load_reports(db_path: Path, report_id: int | None) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if report_id:
            rows = conn.execute(
                "select id, full_report_json from review_reports where id = ?",
                (report_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "select id, full_report_json from review_reports where full_report_json is not null order by id desc limit 20"
            ).fetchall()
    finally:
        conn.close()

    reports: list[dict] = []
    for row in rows:
        try:
            payload = json.loads(row["full_report_json"])
        except json.JSONDecodeError:
            reports.append({"id": row["id"], "error": "corrupted_json"})
            continue
        payload["_stored_report_id"] = row["id"]
        reports.append(payload)
    return reports


def evaluate_report(service: DeepReviewService, report: dict) -> dict:
    stored_id = report.get("_stored_report_id")
    repaired = service.prepare_report_for_display(dict(report))
    quality = repaired.get("quality_audit") or {}
    delivery = repaired.get("delivery_audit") or {}
    workflow = repaired.get("human_review_workflow") or {}
    checks = {item.get("name"): item.get("value") for item in quality.get("checks", []) if isinstance(item, dict)}
    return {
        "report_id": stored_id,
        "meta_report_id": (repaired.get("report_meta") or {}).get("report_id"),
        "strategy_id": checks.get("review_strategy_id"),
        "quality_score": quality.get("quality_score"),
        "quality_level": quality.get("quality_level"),
        "readiness_level": delivery.get("readiness_level"),
        "human_review_status": workflow.get("status"),
        "risk_count": checks.get("risk_count"),
        "verified_citation_count": checks.get("verified_citation_count"),
        "high_risks_without_verified_citation": checks.get("high_risks_without_verified_citation"),
        "generic_favorable_clause_count": checks.get("generic_favorable_clause_count"),
        "incomplete_legal_appendix_count": checks.get("incomplete_legal_appendix_count"),
        "placeholder_revision_plan_count": checks.get("placeholder_revision_plan_count"),
        "warnings": quality.get("warnings", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate deep review report delivery quality.")
    parser.add_argument("--db", default=str(ROOT / "dev.db"), help="SQLite database path.")
    parser.add_argument("--report-id", type=int, default=None, help="Evaluate one stored report id.")
    parser.add_argument("--min-score", type=int, default=70, help="Minimum acceptable quality score.")
    parser.add_argument("--fail-on-low", action="store_true", help="Exit non-zero when a report is below min-score.")
    args = parser.parse_args()

    db_path = Path(args.db)
    reports = load_reports(db_path, args.report_id)
    service = DeepReviewService()
    results = [
        report if report.get("error") else evaluate_report(service, report)
        for report in reports
    ]
    print(json.dumps({"count": len(results), "results": results}, ensure_ascii=False, indent=2))

    if args.fail_on_low and any((item.get("quality_score") or 0) < args.min_score for item in results):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
