from __future__ import annotations

from typing import Any, Dict, Optional


PRODUCT_CATALOG: Dict[str, Dict[str, Any]] = {
    "report_unlock": {
        "sku": "report_unlock",
        "plan_type": None,
        "name": "单份报告解锁",
        "name_en": "Single Report Unlock",
        "description": "解锁一份完整深度审查报告。",
        "description_en": "Unlock one complete deep review report.",
        "amount": 2900,
        "currency": "cny",
        "display_price": "¥29",
        "interval": None,
        "highlight": False,
        "features": ["完整风险条款", "修改建议", "谈判话术", "法律依据引用"],
        "features_en": [
            "Complete risk clauses",
            "Suggested revisions",
            "Negotiation scripts",
            "Legal citation references",
        ],
    },
    "personal_plan": {
        "sku": "personal_plan",
        "plan_type": "personal",
        "name": "个人版",
        "name_en": "Personal",
        "description": "适合个人日常合同审查。",
        "description_en": "For individual contract reviews.",
        "amount": 9900,
        "currency": "cny",
        "display_price": "¥99",
        "interval": "month",
        "highlight": False,
        "report_quota_monthly": 20,
        "team_seats": 1,
        "features": ["每月 20 份审查", "基础风险报告", "PDF 导出", "中英双语"],
        "features_en": ["20 reviews per month", "Basic risk report", "PDF export", "Chinese and English"],
    },
    "lawyer_plan": {
        "sku": "lawyer_plan",
        "plan_type": "lawyer",
        "name": "律师版",
        "name_en": "Lawyer",
        "description": "适合法律从业者高频审查和交付。",
        "description_en": "For legal professionals with frequent review work.",
        "amount": 29900,
        "currency": "cny",
        "display_price": "¥299",
        "interval": "month",
        "highlight": True,
        "report_quota_monthly": 100,
        "team_seats": 5,
        "features": ["每月 100 份审查", "完整报告", "案例与法条引用", "团队协作"],
        "features_en": ["100 reviews per month", "Complete reports", "Case and statute citations", "Team workspace"],
    },
    "enterprise_plan": {
        "sku": "enterprise_plan",
        "plan_type": "enterprise",
        "name": "企业版",
        "name_en": "Enterprise",
        "description": "适合团队批量审查与合规管理。",
        "description_en": "For team review workflows and compliance operations.",
        "amount": 99900,
        "currency": "cny",
        "display_price": "¥999",
        "interval": "month",
        "highlight": False,
        "report_quota_monthly": 1000,
        "team_seats": 50,
        "features": ["每月 1000 份审查", "批量审查", "团队权限", "管理导出"],
        "features_en": ["1000 reviews per month", "Batch review", "Team permissions", "Admin export"],
    },
}

PLAN_LIMITS: Dict[str, Dict[str, Any]] = {
    "free": {
        "report_quota_monthly": 2,
        "team_seats": 1,
        "features": ["basic_review", "pdf_export"],
    },
    "personal": {
        "report_quota_monthly": PRODUCT_CATALOG["personal_plan"]["report_quota_monthly"],
        "team_seats": PRODUCT_CATALOG["personal_plan"]["team_seats"],
        "features": ["deep_review", "pdf_export", "legal_sources"],
    },
    "lawyer": {
        "report_quota_monthly": PRODUCT_CATALOG["lawyer_plan"]["report_quota_monthly"],
        "team_seats": PRODUCT_CATALOG["lawyer_plan"]["team_seats"],
        "features": ["deep_review", "pdf_export", "legal_sources", "templates", "team"],
    },
    "enterprise": {
        "report_quota_monthly": PRODUCT_CATALOG["enterprise_plan"]["report_quota_monthly"],
        "team_seats": PRODUCT_CATALOG["enterprise_plan"]["team_seats"],
        "features": ["deep_review", "pdf_export", "legal_sources", "templates", "team", "admin_export"],
    },
    "admin": {
        "report_quota_monthly": 999999,
        "team_seats": 999,
        "features": ["all"],
    },
}

SKU_TO_PLAN = {
    sku: item["plan_type"]
    for sku, item in PRODUCT_CATALOG.items()
    if item.get("plan_type")
}


def plan_from_sku(sku: Optional[str]) -> Optional[str]:
    return SKU_TO_PLAN.get(sku or "")


def get_sku(sku: str) -> Optional[Dict[str, Any]]:
    item = PRODUCT_CATALOG.get(sku)
    return dict(item) if item else None


def public_product_catalog(locale: str = "zh") -> list[Dict[str, Any]]:
    use_en = locale.lower().startswith("en")
    items: list[Dict[str, Any]] = []
    for item in PRODUCT_CATALOG.values():
        items.append(
            {
                "sku": item["sku"],
                "plan_type": item["plan_type"],
                "name": item["name_en"] if use_en else item["name"],
                "description": item["description_en"] if use_en else item["description"],
                "amount": item["amount"],
                "currency": item["currency"],
                "display_price": item["display_price"],
                "interval": item["interval"],
                "highlight": item["highlight"],
                "features": item["features_en"] if use_en else item["features"],
                "report_quota_monthly": item.get("report_quota_monthly"),
                "team_seats": item.get("team_seats"),
            }
        )
    return items
