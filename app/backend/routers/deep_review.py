# @File: backend/routers/deep_review.py
# @Desc: API routes for deep legal review powered by AI
import logging
import ast
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import db_manager, get_db
from core.auth import AccessTokenError, decode_access_token
from dependencies.auth import get_current_user
from models.prompt_versions import Prompt_versions
from schemas.auth import UserResponse
from services.deep_review import DeepReviewService
from services.document_extraction import DocumentExtractionError, DocumentExtractionService
from services.documents import DocumentsService
from services.entitlements import EntitlementService
from services.review_reports import Review_reportsService
from services.storage import StorageService
from schemas.storage import FileUpDownRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/deep-review", tags=["deep-review"])


# ----------------- Request/Response Models -----------------

class DeepReviewRequest(BaseModel):
    document_text: str
    document_type: str = "合同"
    user_role: str = "甲方"
    review_goal: str = "签署前审查"
    known_facts: Optional[List[str]] = None
    jurisdiction: str = "中国大陆"


class DeepReviewResponse(BaseModel):
    success: bool
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AnalyzeUploadedDocumentRequest(BaseModel):
    document_id: int
    document_type: Optional[str] = None
    user_role: Optional[str] = None
    review_goal: str = "签署前审查"
    known_facts: Optional[List[str]] = None
    jurisdiction: str = "中国大陆"
    bucket_name: str = "law-radar-docs"
    force_reextract: bool = False
    enable_ocr: bool = True


class AnalyzeUploadedDocumentResponse(BaseModel):
    success: bool
    report_id: Optional[int] = None
    review_id: Optional[int] = None
    report: Optional[Dict[str, Any]] = None
    extraction: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AnalyzeUploadedDocumentStartResponse(BaseModel):
    success: bool
    document_id: int
    status: str
    message: str
    error: Optional[str] = None


class AnalyzeUploadedDocumentStatusResponse(BaseModel):
    success: bool
    document_id: int
    status: str
    report_id: Optional[int] = None
    review_id: Optional[int] = None
    extraction: Optional[Dict[str, Any]] = None
    progress: Optional[Dict[str, Any]] = None
    pipeline_preview: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    message: Optional[str] = None


class GenerateDocumentRequest(BaseModel):
    doc_type: str
    user_role: str = "甲方"
    title: str = ""
    input_data: Dict[str, Any] = {}
    language: str = "zh"


class GenerateDocumentResponse(BaseModel):
    success: bool
    document: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CaseAIChatRequest(BaseModel):
    case_context: str
    user_message: str
    conversation_history: Optional[List[Dict[str, str]]] = None


class CaseAIChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def _risk_score_from_report(report: Dict[str, Any]) -> Optional[int]:
    scoring = report.get("risk_scoring") if isinstance(report.get("risk_scoring"), dict) else {}
    meta = report.get("report_meta") if isinstance(report.get("report_meta"), dict) else {}
    for value in (scoring.get("overall_score"), meta.get("risk_score")):
        try:
            if value is not None and value != "":
                return int(round(float(value)))
        except (TypeError, ValueError):
            continue
    return None


_RUNNING_REVIEW_PROGRESS: dict[str, dict[str, Any]] = {}


def _review_progress_key(user_id: str, document_id: int) -> str:
    return f"{user_id}:{document_id}"


def _set_review_progress(
    *,
    user_id: str,
    document_id: int,
    phase: str,
    stage_id: str,
    stage_name: str,
    detail: str,
    percent: int,
    status: str = "running",
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    key = _review_progress_key(user_id, document_id)
    previous = _RUNNING_REVIEW_PROGRESS.get(key, {})
    completed = list(previous.get("completed_stages") or [])
    if status == "completed" and stage_id and not any(item.get("stage_id") == stage_id for item in completed):
        completed.append(
            {
                "stage_id": stage_id,
                "stage_name": stage_name,
                "completed_at": datetime.utcnow().isoformat(),
            }
        )
    payload: dict[str, Any] = {
        "phase": phase,
        "stage_id": stage_id,
        "stage_name": stage_name,
        "detail": detail,
        "percent": max(0, min(100, int(percent))),
        "status": status,
        "updated_at": datetime.utcnow().isoformat(),
        "completed_stages": completed[-12:],
    }
    if extra:
        payload.update(extra)
    _RUNNING_REVIEW_PROGRESS[key] = payload
    return payload


def _get_review_progress(user_id: str, document_id: int, status: str) -> dict[str, Any]:
    active = _RUNNING_REVIEW_PROGRESS.get(_review_progress_key(user_id, document_id))
    if active:
        return active
    fallback = {
        "queued": ("queued", "任务排队中", "后台任务已创建，等待开始解析文档。", 24),
        "processing": ("queued", "任务准备中", "正在准备深度审查任务。", 18),
        "extracting": ("extracting", "解析/OCR", "正在提取文本层；扫描页会进入 OCR。", 38),
        "analyzing": ("analyzing", "深度法律审查", "正在执行多阶段法律审查，页面会继续刷新具体状态。", 58),
        "completed": ("completed", "报告已生成", "深度审查报告已生成。", 100),
        "failed": ("failed", "审查失败", "深度审查失败，请查看错误信息。", 100),
    }
    phase, stage_name, detail, percent = fallback.get(status or "", fallback["processing"])
    return {
        "phase": phase,
        "stage_id": phase,
        "stage_name": stage_name,
        "detail": detail,
        "percent": percent,
        "status": status or "processing",
        "updated_at": datetime.utcnow().isoformat(),
        "completed_stages": [],
    }


async def _active_review_prompt_extension(db: AsyncSession) -> str:
    result = await db.execute(
        select(Prompt_versions)
        .where(Prompt_versions.purpose == "deep_review")
        .where(Prompt_versions.is_active.is_(True))
        .order_by(Prompt_versions.id.desc())
        .limit(1)
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        return ""
    parts = [
        f"版本名称：{prompt.name}",
        f"版本号：{prompt.version}",
        f"状态：{prompt.status or 'active'}",
        "系统 Prompt：",
        prompt.system_prompt,
    ]
    if prompt.user_prompt:
        parts.extend(["用户 Prompt 补充：", prompt.user_prompt])
    return "\n".join(str(part) for part in parts if part is not None)


async def _persist_deep_report(
    *,
    db: AsyncSession,
    user_id: str,
    document_id: int,
    report: Dict[str, Any],
) -> tuple[int, int]:
    report_service = Review_reportsService(db)

    meta = report.get("report_meta") or {}
    summary = report.get("executive_summary") or {}
    risk_score = _risk_score_from_report(report)

    review_report = await report_service.create(
        {
            "document_id": document_id,
            "contract_type": meta.get("document_type"),
            "risk_score": risk_score,
            "user_role": meta.get("user_role"),
            "risk_level": meta.get("overall_risk_level"),
            "signing_recommendation": meta.get("recommendation"),
            "executive_summary": _json_dumps(summary),
            "contract_basic_info": _json_dumps(report.get("contract_summary") or {}),
            "risk_matrix": _json_dumps(report.get("risk_matrix") or []),
            "missing_clause_checklist": _json_dumps(report.get("missing_clauses") or []),
            "favorable_clauses": _json_dumps(report.get("favorable_clauses") or []),
            "legal_source_appendix": _json_dumps(report.get("legal_authority_appendix") or []),
            "full_report_json": _json_dumps(report),
            "pipeline_trace_json": _json_dumps(report.get("pipeline_trace") or []),
            "disclaimer": report.get("disclaimer"),
            "status": "completed",
            "is_paid": False,
        },
        user_id=user_id,
    )

    return review_report.id, review_report.id


def _parse_extraction_info(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _status_message(status: str) -> str:
    messages = {
        "queued": "审查任务已进入队列。",
        "extracting": "正在解析文档文本并按需执行 OCR。",
        "analyzing": "正在执行深度法律审查，模型会分阶段生成风险、依据和修改建议。",
        "completed": "深度审查报告已生成。",
        "failed": "深度审查失败，请查看错误信息。",
    }
    return messages.get(status or "", "审查状态待更新。")


def _json_loads_or(raw: Optional[str], fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _summary_text(summary: Dict[str, Any], risk_level: Optional[str]) -> str:
    top_risks = [str(item) for item in summary.get("top_risks") or [] if item]
    if top_risks:
        return "；".join(top_risks[:3])
    priority_actions = [str(item) for item in summary.get("priority_actions") or [] if item]
    if priority_actions:
        return "；".join(priority_actions[:3])
    return f"深度审查完成：总体风险等级 {risk_level or '中'}。"


def _report_payload_from_record(stored: Any) -> Dict[str, Any]:
    report = _json_loads_or(stored.full_report_json, {})
    if isinstance(report, dict) and report:
        report = DeepReviewService().prepare_report_for_display(report)
    else:
        report = {}

    meta = report.get("report_meta") if isinstance(report.get("report_meta"), dict) else {}
    summary = report.get("executive_summary") if isinstance(report.get("executive_summary"), dict) else {}
    risk_items = report.get("risk_items") if isinstance(report.get("risk_items"), list) else []
    top_risks = summary.get("top_risks") if isinstance(summary.get("top_risks"), list) else []
    if not top_risks:
        top_risks = [
            {
                "title": risk.get("title"),
                "severity": risk.get("risk_level"),
            }
            for risk in risk_items[:5]
            if isinstance(risk, dict)
        ]

    missing_clauses = report.get("missing_clauses")
    if not isinstance(missing_clauses, list):
        missing_clauses = _json_loads_or(stored.missing_clause_checklist, [])
    favorable_clauses = report.get("favorable_clauses")
    if not isinstance(favorable_clauses, list):
        favorable_clauses = _json_loads_or(stored.favorable_clauses, [])
    pipeline_trace = _json_loads_or(stored.pipeline_trace_json, report.get("pipeline_trace") or [])

    risk_level = meta.get("overall_risk_level") or stored.risk_level
    risk_score = stored.risk_score if stored.risk_score is not None else _risk_score_from_report(report)
    return {
        "success": True,
        "report_id": stored.id,
        "review_id": stored.id,
        "document_id": stored.document_id,
        "status": stored.status,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "signing_recommendation": meta.get("recommendation") or stored.signing_recommendation,
        "executive_summary": _summary_text(summary, risk_level),
        "summary": summary,
        "top_risks": top_risks,
        "citation_audit": report.get("citation_audit") if isinstance(report.get("citation_audit"), dict) else {},
        "evidence_audit": report.get("evidence_audit") if isinstance(report.get("evidence_audit"), dict) else {},
        "risk_scoring": report.get("risk_scoring") if isinstance(report.get("risk_scoring"), dict) else {},
        "risk_items": risk_items,
        "missing_clauses": missing_clauses,
        "favorable_clauses": favorable_clauses,
        "next_steps": summary.get("priority_actions") or [],
        "pipeline_trace": pipeline_trace,
        "is_paid": bool(stored.is_paid),
        "created_at": stored.created_at,
        "updated_at": stored.updated_at,
    }


def _pipeline_payload_from_record(stored: Any) -> Dict[str, Any]:
    report = _json_loads_or(stored.full_report_json, {})
    trace = _json_loads_or(stored.pipeline_trace_json, [])
    if not trace and isinstance(report, dict):
        trace = report.get("pipeline_trace") or []
    total_duration_ms = sum(
        int(stage.get("duration_ms") or 0)
        for stage in trace
        if isinstance(stage, dict)
    )
    return {
        "success": True,
        "report_id": stored.id,
        "document_id": stored.document_id,
        "status": stored.status,
        "generated_at": stored.created_at,
        "total_duration_ms": total_duration_ms,
        "trace": trace,
    }


def _safe_filename(value: str, fallback: str = "deep-review-report") -> str:
    name = re.sub(r'[\\/:*?"<>|\r\n]+', "_", str(value or "").strip())
    return name[:80] or fallback


def _user_from_access_token(token: str) -> UserResponse:
    try:
        payload = decode_access_token(token)
    except AccessTokenError as exc:
        raise HTTPException(status_code=401, detail=exc.message) from exc
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return UserResponse(
        id=user_id,
        email=payload.get("email", ""),
        name=payload.get("name"),
        role=payload.get("role", "user"),
        last_login=None,
    )


async def get_export_user(request: Request) -> UserResponse:
    """Export endpoint auth: header token for API calls, query token for browser downloads."""
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return _user_from_access_token(authorization.split(" ", 1)[1].strip())
    token = request.query_params.get("download_token") or request.query_params.get("token")
    if token:
        return _user_from_access_token(token)
    raise HTTPException(status_code=401, detail="Authentication credentials were not provided")


def _report_to_markdown(report: Dict[str, Any]) -> str:
    meta = report.get("report_meta") or {}
    summary = report.get("executive_summary") or {}
    contract = report.get("contract_summary") or {}
    lines: list[str] = []
    lines.append(f"# 深度法律审查报告 {meta.get('report_id', '')}".strip())
    lines.append("")
    lines.append(f"- 生成时间：{meta.get('generated_at', '')}")
    lines.append(f"- 文书类型：{meta.get('document_type', '')}")
    lines.append(f"- 审查立场：{meta.get('user_role', '')}")
    lines.append(f"- 法域：{meta.get('jurisdiction', '')}")
    lines.append(f"- 总体风险：{meta.get('overall_risk_level', '')}")
    lines.append(f"- 签署建议：{meta.get('recommendation', '')}")
    lines.append("")

    lines.append("## 执行摘要")
    for item in summary.get("top_risks") or []:
        lines.append(f"- 核心风险：{item}")
    for item in summary.get("priority_actions") or []:
        lines.append(f"- 优先动作：{item}")
    lines.append("")

    lines.append("## 合同结构摘要")
    lines.append(f"- 合同目的：{contract.get('purpose', '')}")
    lines.append(f"- 付款/金额：{contract.get('payment_terms', '')}")
    lines.append(f"- 期限：{contract.get('term', '')}")
    lines.append(f"- 争议解决：{contract.get('dispute_resolution', '')}")
    for item in contract.get("main_obligations") or []:
        lines.append(f"- 主要义务：{item}")
    lines.append("")

    lines.append("## 风险项")
    for risk in report.get("risk_items") or []:
        if not isinstance(risk, dict):
            continue
        analysis = risk.get("legal_analysis") if isinstance(risk.get("legal_analysis"), dict) else {}
        revision = risk.get("revision_plan") if isinstance(risk.get("revision_plan"), dict) else {}
        original = risk.get("original_clause") if isinstance(risk.get("original_clause"), dict) else {}
        lines.append(f"### {risk.get('risk_id', '')} {risk.get('title', '')}")
        lines.append(f"- 等级：{risk.get('risk_level', '')}")
        lines.append(f"- 位置：{original.get('clause_number', '')}")
        lines.append(f"- 原文：{original.get('text', '')}")
        lines.append(f"- 分析：{analysis.get('application_to_clause', '') or analysis.get('applicable_rule', '')}")
        lines.append(f"- 影响：{analysis.get('user_impact', '')}")
        lines.append(f"- 建议条款：{revision.get('balanced_clause', '') or revision.get('conservative_clause', '')}")
        citations = risk.get("citations") or []
        if citations:
            citation_text = "；".join(
                f"{c.get('source_name', '')}{c.get('article_or_case_number', '')}"
                for c in citations
                if isinstance(c, dict)
            )
            lines.append(f"- 法律依据：{citation_text}")
        lines.append("")

    lines.append("## 缺失条款")
    missing = [item for item in report.get("missing_clauses") or [] if isinstance(item, dict)]
    if missing:
        for item in missing:
            lines.append(f"### {item.get('name', '')}")
            lines.append(f"- 风险：{item.get('risk', '')}")
            lines.append(f"- 建议补充：{item.get('recommended_clause', '')}")
            if item.get("citations"):
                lines.append(f"- 法律依据：{'、'.join(str(c) for c in item.get('citations') or [])}")
            lines.append("")
    else:
        lines.append("未识别到明确缺失条款。")
        lines.append("")

    lines.append("## 有利条款")
    favorable = [item for item in report.get("favorable_clauses") or [] if isinstance(item, dict)]
    if favorable:
        for item in favorable:
            lines.append(f"- {item.get('clause_reference', '')}：{item.get('reason', '')}；建议：{item.get('keep_or_modify', '')}")
    else:
        lines.append("未识别到可以直接保留且对当前立场明确有利的完整条款。")
    lines.append("")

    lines.append("## 法律依据附录")
    for source in report.get("legal_authority_appendix") or []:
        if not isinstance(source, dict):
            continue
        lines.append(
            f"- {source.get('source_name', '')}{source.get('article_or_case_number', '')}："
            f"{source.get('text_excerpt_or_holding', '')} "
            f"（{source.get('authority_level', '')}，{source.get('verification_status', '')}）"
        )
    lines.append("")

    delivery = report.get("delivery_audit") if isinstance(report.get("delivery_audit"), dict) else {}
    if delivery:
        lines.append("## 交付质量审计")
        lines.append(f"- 交付定位：{delivery.get('positioning', '')}")
        lines.append(f"- 交付状态：{delivery.get('readiness_level', '')}")
        for issue in delivery.get("blocking_issues") or []:
            lines.append(f"- 阻断/提示：{issue}")
        lines.append("")

    workflow = report.get("human_review_workflow") if isinstance(report.get("human_review_workflow"), dict) else {}
    if workflow:
        lines.append("## 人工复核任务包")
        lines.append(f"- 复核状态：{workflow.get('status', '')}")
        lines.append(f"- 分诊级别：{workflow.get('triage_level', '')}")
        for task in workflow.get("review_tasks") or []:
            if isinstance(task, dict):
                lines.append(f"- {task.get('task_id', '')} {task.get('title', '')}（{task.get('owner_role', '')}）")
        lines.append("")

    lines.append("## 免责声明")
    lines.append(report.get("disclaimer") or "")
    lines.append("")
    return "\n".join(lines)


def _report_to_doc_html(report: Dict[str, Any]) -> str:
    markdown = _report_to_markdown(report)
    body = []
    for line in markdown.splitlines():
        escaped = (
            line.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        if escaped.startswith("# "):
            body.append(f"<h1>{escaped[2:]}</h1>")
        elif escaped.startswith("## "):
            body.append(f"<h2>{escaped[3:]}</h2>")
        elif escaped.startswith("### "):
            body.append(f"<h3>{escaped[4:]}</h3>")
        elif escaped.startswith("- "):
            body.append(f"<p>{escaped}</p>")
        elif escaped:
            body.append(f"<p>{escaped}</p>")
        else:
            body.append("<p></p>")
    return (
        "<html><head><meta charset='utf-8'>"
        "<style>body{font-family:Microsoft YaHei,SimSun,sans-serif;line-height:1.7;color:#111827;}"
        "h1{font-size:24px;}h2{font-size:18px;border-bottom:1px solid #e5e7eb;padding-bottom:4px;}"
        "h3{font-size:15px;color:#1f2937;}p{font-size:12px;margin:6px 0;}</style>"
        "</head><body>"
        + "".join(body)
        + "</body></html>"
    )


def _pdf_font_path() -> Optional[str]:
    candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\NotoSansSC-VF.ttf",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _clean_pdf_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "；".join(_clean_pdf_text(item) for item in value if _clean_pdf_text(item))
    if isinstance(value, dict):
        labels = {
            "field": "事项",
            "reason": "原因",
            "impact": "影响",
            "action": "建议动作",
            "risk_impact": "风险影响",
            "source": "来源",
        }
        return "；".join(
            f"{labels.get(str(key), str(key))}：{_clean_pdf_text(val)}"
            for key, val in value.items()
            if str(key) != "source" and _clean_pdf_text(val)
        )
    text = str(value)
    stripped = text.strip()
    if stripped.startswith(("{", "[")) and stripped.endswith(("}", "]")):
        try:
            parsed = ast.literal_eval(stripped)
            if parsed is not value:
                return _clean_pdf_text(parsed)
        except Exception:
            pass
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = re.sub(
        r"(?<![A-Za-z0-9])(?:[A-Za-z0-9]\s+){2,}[A-Za-z0-9](?![A-Za-z0-9])",
        lambda match: re.sub(r"\s+", "", match.group(0)),
        text,
    )
    text = re.sub(r"(?<=\b\d)\s+(?=\d\b)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clip_pdf_text(value: Any, limit: int = 1200) -> str:
    text = _clean_pdf_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _format_pdf_datetime(value: Any) -> str:
    text = _clean_pdf_text(value)
    if not text:
        return ""
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return text.replace("T", " ")[:16]


def _cover_recommendation(value: Any, limit: int = 120) -> str:
    text = _clean_pdf_text(value) or "修改后签署"
    if len(text) <= limit:
        return text
    for mark in ("。", "；", ";"):
        cut = text.rfind(mark, 0, limit)
        if cut >= 48:
            return text[: cut + 1]
    return text[: limit - 1].rstrip("，,；;、 ") + "。"


def _risk_pdf_color(level: str) -> tuple[float, float, float]:
    normalized = str(level or "")
    if "重大" in normalized or "高" in normalized or normalized.lower() == "high":
        return (0.72, 0.17, 0.13)
    if "中" in normalized or normalized.lower() == "medium":
        return (0.73, 0.42, 0.07)
    return (0.05, 0.43, 0.31)


def _report_to_pdf_bytes(report: Dict[str, Any]) -> bytes:
    try:
        import fitz
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("当前后端未安装 PyMuPDF，无法导出 PDF。") from exc

    doc = fitz.open()
    width, height = 595, 842
    margin_x = 54
    top_y = 66
    bottom_y = 780
    y = top_y
    page = doc.new_page(width=width, height=height)
    font_path = _pdf_font_path()
    font_name = "LawRadarSC" if font_path else "china-s"
    measure_font = fitz.Font(fontfile=font_path) if font_path else fitz.Font(fontname="china-s")

    ink = (0.06, 0.07, 0.08)
    muted = (0.38, 0.40, 0.43)
    hairline = (0.76, 0.76, 0.73)
    paper = (1.0, 1.0, 0.99)
    panel = (0.965, 0.962, 0.945)
    accent = (0.02, 0.31, 0.26)

    def mostly_latin(text: str) -> bool:
        if not text:
            return False
        if any((not char.isascii()) and (not char.isspace()) for char in text):
            return False
        latin = sum(1 for char in text if char.isascii() and (char.isalnum() or char in " .,;:()[]/%+-_$#'\""))
        visible = sum(1 for char in text if not char.isspace())
        return visible > 0 and latin / visible >= 0.86

    def display_units(text: str) -> float:
        units = 0.0
        for char in text:
            if char.isspace():
                units += 0.30
            elif char.isascii() and char.isalnum():
                units += 0.55
            elif char.isascii():
                units += 0.35
            elif char in "®™≤≥":
                units += 0.65
            else:
                units += 1.0
        return units

    def put_text(x: float, baseline: float, text: str, size: float, color: tuple[float, float, float] = ink) -> None:
        clean = _clean_pdf_text(text)
        if not clean:
            return
        if mostly_latin(clean):
            try:
                page.insert_text((x, baseline), clean, fontsize=size, fontname="helv", color=color)
                return
            except Exception:
                pass
        kwargs: dict[str, Any] = {"fontsize": size, "fontname": font_name, "color": color}
        if font_path:
            kwargs["fontfile"] = font_path
        page.insert_text((x, baseline), clean, **kwargs)

    def text_width(text: str, size: float) -> float:
        clean = _clean_pdf_text(text)
        try:
            measured = measure_font.text_length(clean, fontsize=size)
        except Exception:
            measured = 0
        conservative = display_units(clean) * size
        return max(measured, conservative) * 1.04

    def wrap_line(text: str, size: float, max_width: float) -> list[str]:
        text = _clean_pdf_text(text)
        if not text:
            return [""]
        tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_./:%+,\-()#]*|\s+|.", text)
        lines: list[str] = []
        line = ""

        def append_token(current: str, token: str) -> tuple[str, list[str]]:
            emitted: list[str] = []
            if token.isspace():
                return (current + " " if current and not current.endswith(" ") else current), emitted
            candidate = f"{current}{token}"
            if text_width(candidate, size) <= max_width:
                return candidate, emitted
            if current.strip():
                emitted.append(current.rstrip())
                current = ""
            if text_width(token, size) <= max_width:
                return token, emitted
            piece = ""
            for char in token:
                if text_width(piece + char, size) > max_width and piece:
                    emitted.append(piece)
                    piece = char
                else:
                    piece += char
            return piece, emitted

        for token in tokens:
            line, emitted_lines = append_token(line, token)
            lines.extend(emitted_lines)
        if line.strip():
            lines.append(line.rstrip())
        return lines or [text]

    def wrapped_lines(text: Any, size: float, max_width: float) -> list[str]:
        lines: list[str] = []
        for paragraph in _clean_pdf_text(text).splitlines() or [""]:
            if not paragraph.strip():
                lines.append("")
                continue
            lines.extend(wrap_line(paragraph, size, max_width))
        return lines

    def estimate_height(text: Any, size: float, max_width: float, line_height: float = 1.55) -> float:
        return max(1, len(wrapped_lines(text, size, max_width))) * size * line_height

    def paint_page_background() -> None:
        page.draw_rect(fitz.Rect(0, 0, width, height), color=paper, fill=paper, width=0)

    def paint_header() -> None:
        put_text(margin_x, 36, "律审雷达  LAWAUDIT RADAR", 9, muted)
        page.draw_line((margin_x, 48), (width - margin_x, 48), color=hairline, width=0.55)

    def new_page(with_header: bool = True) -> None:
        nonlocal page, y
        page = doc.new_page(width=width, height=height)
        paint_page_background()
        if with_header:
            paint_header()
            y = top_y
        else:
            y = margin_x

    def ensure_space(needed: float) -> None:
        if y + needed > bottom_y:
            new_page()

    def draw_text(
        text: Any,
        *,
        size: float = 10,
        color: tuple[float, float, float] = ink,
        x: Optional[float] = None,
        max_width: Optional[float] = None,
        line_height: float = 1.55,
        gap: float = 7,
    ) -> None:
        nonlocal y
        left = margin_x if x is None else x
        available = width - margin_x - left if max_width is None else max_width
        for line in wrapped_lines(text, size, available):
            if not line:
                y += size * 0.65
                continue
            ensure_space(size * line_height + gap)
            put_text(left, y, line, size, color)
            y += size * line_height
        y += gap

    def draw_section(title: str) -> None:
        nonlocal y
        ensure_space(42)
        y += 6
        page.draw_line((margin_x, y), (width - margin_x, y), color=hairline, width=0.65)
        y += 22
        put_text(margin_x, y, title, 15, ink)
        y += 20

    def draw_small_label(label: str, value: Any, *, max_chars: int = 500) -> None:
        nonlocal y
        text = _clip_pdf_text(value, max_chars)
        if not text:
            return
        ensure_space(min(170, 22 + estimate_height(text, 9.5, width - margin_x * 2)))
        put_text(margin_x, y, label, 8.5, accent)
        y += 13
        draw_text(text, size=9.5, color=ink, gap=9)

    def draw_bullet(text: Any) -> None:
        nonlocal y
        clean = _clip_pdf_text(text, 900)
        if not clean:
            return
        lines = wrapped_lines(clean, 9.5, width - margin_x * 2 - 16)
        ensure_space(len(lines) * 15 + 4)
        put_text(margin_x, y, "•", 11, accent)
        start_y = y
        for idx, line in enumerate(lines):
            if idx and y + 15 > bottom_y:
                new_page()
                start_y = y
            put_text(margin_x + 16, y, line, 9.5, ink)
            y += 15
        if y == start_y:
            y += 15
        y += 4

    def draw_quote(text: Any) -> None:
        nonlocal y
        clean = _clip_pdf_text(text, 1600)
        if not clean:
            return
        quote_width = width - margin_x * 2
        quote_height = min(190, estimate_height(clean, 8.7, quote_width - 22) + 18)
        ensure_space(quote_height + 8)
        page.draw_rect(
            fitz.Rect(margin_x, y - 11, width - margin_x, y + quote_height - 8),
            color=(0.82, 0.82, 0.78),
            fill=(0.985, 0.984, 0.970),
            width=0.45,
        )
        y += 4
        draw_text(clean, size=8.7, color=(0.18, 0.21, 0.26), x=margin_x + 11, max_width=quote_width - 22, gap=12)

    def draw_meta_table(items: list[tuple[str, Any]]) -> None:
        nonlocal y
        col_w = (width - margin_x * 2) / 2
        row_h = 44
        for row_idx in range(0, len(items), 2):
            ensure_space(row_h + 6)
            for col_idx, (label, value) in enumerate(items[row_idx : row_idx + 2]):
                x = margin_x + col_idx * col_w
                page.draw_rect(
                    fitz.Rect(x, y - 13, x + col_w - 8, y + row_h - 13),
                    color=(0.82, 0.82, 0.78),
                    fill=(0.990, 0.988, 0.975),
                    width=0.45,
                )
                put_text(x + 10, y, label, 7.8, muted)
                value_lines = wrapped_lines(_clip_pdf_text(value, 96) or "-", 8.8, col_w - 26)[:2]
                for line_index, line in enumerate(value_lines):
                    put_text(x + 10, y + 15 + line_index * 12, line, 8.8, ink)
            y += row_h + 6

    def draw_risk_item(index: int, risk: dict[str, Any]) -> None:
        nonlocal y
        title = _clean_pdf_text(risk.get("title")) or f"风险项 {index}"
        level = _clean_pdf_text(risk.get("risk_level")) or "中"
        original = risk.get("original_clause") if isinstance(risk.get("original_clause"), dict) else {}
        analysis = risk.get("legal_analysis") if isinstance(risk.get("legal_analysis"), dict) else {}
        revision = risk.get("revision_plan") if isinstance(risk.get("revision_plan"), dict) else {}
        ensure_space(76)
        risk_color = _risk_pdf_color(level)
        page.draw_rect(
            fitz.Rect(margin_x, y - 13, width - margin_x, y + 37),
            color=(0.80, 0.80, 0.76),
            fill=(0.990, 0.988, 0.975),
            width=0.45,
        )
        page.draw_rect(fitz.Rect(margin_x, y - 13, margin_x + 5, y + 37), color=risk_color, fill=risk_color, width=0)
        put_text(margin_x + 14, y, _clip_pdf_text(f"{risk.get('risk_id') or f'R-{index:03d}'}  {title}", 82), 11.2, ink)
        put_text(width - margin_x - 60, y, f"等级：{level}", 8.8, risk_color)
        put_text(margin_x + 14, y + 18, f"位置：{_clip_pdf_text(original.get('clause_number') or risk.get('clause_reference') or '未稳定定位', 80)}", 8.4, muted)
        y += 54
        draw_small_label("原条款摘录（节选）", original.get("text") or original.get("original_text") or risk.get("issue_location"), max_chars=720)
        draw_small_label("法律分析", analysis.get("application_to_clause") or analysis.get("applicable_rule") or risk.get("issue_location"), max_chars=1400)
        draw_small_label("用户影响", analysis.get("user_impact"), max_chars=900)
        draw_small_label("建议修改", revision.get("balanced_clause") or revision.get("conservative_clause") or revision.get("bottom_line_clause"), max_chars=1400)
        strategy = revision.get("negotiation_strategy")
        if strategy:
            draw_small_label("谈判策略", strategy, max_chars=900)

    meta = report.get("report_meta") or {}
    summary = report.get("executive_summary") or {}
    contract = report.get("contract_summary") or {}
    risk_items = [item for item in report.get("risk_items") or [] if isinstance(item, dict)]
    missing_clauses = [item for item in report.get("missing_clauses") or [] if isinstance(item, dict)]
    favorable_clauses = [item for item in report.get("favorable_clauses") or [] if isinstance(item, dict)]
    legal_sources = [item for item in report.get("legal_authority_appendix") or [] if isinstance(item, dict)]
    delivery = report.get("delivery_audit") if isinstance(report.get("delivery_audit"), dict) else {}

    paint_page_background()
    cover_y = 78
    put_text(margin_x, cover_y, "律审雷达", 20, ink)
    put_text(margin_x, cover_y + 18, "LAWAUDIT RADAR | LEGAL REVIEW MEMORANDUM", 8.5, muted)
    page.draw_line((margin_x, cover_y + 42), (width - margin_x, cover_y + 42), color=hairline, width=0.65)
    put_text(margin_x, cover_y + 92, "法律风险审查报告", 26, ink)
    put_text(margin_x, cover_y + 122, _clean_pdf_text(meta.get("report_id") or "Deep Review Report"), 10, muted)
    risk_level = _clean_pdf_text(meta.get("overall_risk_level") or "中")
    risk_color = _risk_pdf_color(risk_level)
    page.draw_rect(
        fitz.Rect(margin_x, cover_y + 160, width - margin_x, cover_y + 310),
        color=(0.78, 0.78, 0.74),
        fill=panel,
        width=0.55,
    )
    put_text(margin_x + 18, cover_y + 190, "总体风险", 8.5, muted)
    put_text(margin_x + 18, cover_y + 222, risk_level, 26, risk_color)
    put_text(margin_x + 160, cover_y + 190, "签署建议", 8.5, muted)
    saved_y = y
    y = cover_y + 222
    draw_text(
        _cover_recommendation(meta.get("recommendation")),
        size=12.4,
        x=margin_x + 160,
        max_width=width - margin_x * 2 - 178,
        line_height=1.3,
        gap=0,
    )
    y = saved_y
    y = cover_y + 348
    draw_meta_table(
        [
            ("文书类型", meta.get("document_type")),
            ("审查立场", meta.get("user_role")),
            ("法域", meta.get("jurisdiction")),
            ("生成时间", _format_pdf_datetime(meta.get("generated_at"))),
            ("审查策略", meta.get("review_strategy_name")),
            ("专业等级", meta.get("professional_grade")),
        ]
    )
    y += 8
    put_text(margin_x, y, "核心摘要", 12, ink)
    y += 20
    for item in (summary.get("top_risks") or [])[:4]:
        draw_bullet(item)

    new_page()
    draw_section("一、执行摘要")
    for item in summary.get("top_risks") or []:
        draw_bullet(f"核心风险：{_clean_pdf_text(item)}")
    for item in summary.get("priority_actions") or []:
        draw_bullet(f"优先动作：{_clean_pdf_text(item)}")
    for item in (summary.get("missing_facts") or [])[:8]:
        draw_bullet(f"待补事实：{_clean_pdf_text(item)}")

    draw_section("二、文书结构摘要")
    draw_meta_table(
        [
            ("合同目的", contract.get("purpose")),
            ("付款/金额", contract.get("payment_terms")),
            ("履行期限", contract.get("term")),
            ("争议解决", contract.get("dispute_resolution")),
        ]
    )
    obligations = contract.get("main_obligations") or []
    if obligations:
        put_text(margin_x, y, "主要义务/审查重点", 10, accent)
        y += 16
        for item in obligations[:8]:
            draw_bullet(item)

    if delivery:
        draw_section("三、交付质量审计")
        draw_meta_table(
            [
                ("交付定位", delivery.get("positioning")),
                ("交付状态", delivery.get("readiness_level")),
                ("风险项数量", delivery.get("risk_count")),
                ("法律依据数量", delivery.get("legal_source_count")),
            ]
        )
        for issue in delivery.get("blocking_issues") or []:
            draw_bullet(issue)

    draw_section("四、风险项")
    if risk_items:
        for index, risk in enumerate(risk_items, start=1):
            draw_risk_item(index, risk)
    else:
        draw_text("未识别到明确风险项。", size=10, color=muted)

    draw_section("五、缺失条款")
    if missing_clauses:
        for item in missing_clauses:
            ensure_space(48)
            put_text(margin_x, y, _clean_pdf_text(item.get("name") or "缺失条款"), 11, ink)
            y += 17
            draw_small_label("风险", item.get("risk"), max_chars=900)
            draw_small_label("建议补充", item.get("recommended_clause"), max_chars=1200)
    else:
        draw_text("未识别到明确缺失条款。", size=10, color=muted)

    draw_section("六、有利条款")
    if favorable_clauses:
        for item in favorable_clauses:
            draw_bullet(
                f"{item.get('clause_reference') or '条款'}："
                f"{item.get('reason') or ''}"
                f"；建议：{item.get('keep_or_modify') or '保留并复核'}"
            )
    else:
        draw_text("未识别到可以直接保留且对当前立场明确有利的完整条款。", size=10, color=muted)

    draw_section("七、法律依据附录")
    if legal_sources:
        for source in legal_sources[:40]:
            title = f"{source.get('source_name') or '法律依据'}{source.get('article_or_case_number') or ''}"
            put_text(margin_x, y, _clip_pdf_text(title, 90), 10.2, ink)
            y += 16
            draw_text(
                f"{source.get('text_excerpt_or_holding') or source.get('legal_effect_note') or ''}"
                f"（{source.get('authority_level') or ''}，{source.get('verification_status') or ''}）",
                size=8.7,
                color=muted,
                gap=8,
            )
    else:
        draw_text("暂无可展示的法律依据。", size=10, color=muted)

    draw_section("八、免责声明")
    draw_text(report.get("disclaimer") or "本报告为 AI 辅助生成的风险提示，不构成正式法律意见。", size=9.2, color=muted)

    page_count = doc.page_count
    for index, pdf_page in enumerate(doc, start=1):
        pdf_page.draw_line((margin_x, 804), (width - margin_x, 804), color=hairline, width=0.45)
        kwargs: dict[str, Any] = {"fontsize": 7.5, "fontname": font_name, "color": muted}
        if font_path:
            kwargs["fontfile"] = font_path
        pdf_page.insert_text((margin_x, 820), "AI 辅助审查报告，仅供参考，不构成正式法律意见。", **kwargs)
        pdf_page.insert_text((width - margin_x - 54, 820), f"{index} / {page_count}", **kwargs)

    payload = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return payload


async def _run_uploaded_document_review(
    *,
    db: AsyncSession,
    document: Any,
    data: AnalyzeUploadedDocumentRequest,
    user_id: str,
    user_role: str = "user",
) -> AnalyzeUploadedDocumentResponse:
    documents_service = DocumentsService(db)
    extraction_info: Dict[str, Any] = {}

    async def publish_progress(event: dict[str, Any]) -> None:
        _set_review_progress(
            user_id=user_id,
            document_id=document.id,
            phase=str(event.get("phase") or "analyzing"),
            stage_id=str(event.get("stage_id") or "analyzing"),
            stage_name=str(event.get("stage_name") or "深度法律审查"),
            detail=str(event.get("detail") or "正在执行深度法律审查。"),
            percent=int(event.get("percent") or 58),
            status=str(event.get("status") or "running"),
            extra={k: v for k, v in event.items() if k not in {"phase", "stage_id", "stage_name", "detail", "percent", "status"}},
        )

    try:
        _set_review_progress(
            user_id=user_id,
            document_id=document.id,
            phase="extracting",
            stage_id="storage-download",
            stage_name="读取上传文件",
            detail="正在从文档存储读取原始文件。若文件较大，这一步可能需要几十秒。",
            percent=28,
        )
        if document.extracted_text and not data.force_reextract:
            document_text = document.extracted_text
            extraction_info = {
                "parser": "cached",
                "char_count": len(document_text),
                "warnings": [],
            }
            _set_review_progress(
                user_id=user_id,
                document_id=document.id,
                phase="extracting",
                stage_id="cached-text",
                stage_name="使用已解析文本",
                detail="检测到文档已有可用正文，跳过重复 OCR，准备进入法律审查。",
                percent=36,
                status="completed",
            )
            await documents_service.update(
                document.id,
                {
                    "status": "analyzing",
                    "extraction_error": "",
                },
                user_id=user_id,
            )
        else:
            if not document.file_key:
                raise HTTPException(status_code=400, detail="Document has no file_key and no extracted_text.")

            await documents_service.update(
                document.id,
                {
                    "status": "extracting",
                    "extraction_error": "",
                },
                user_id=user_id,
            )
            storage_service = StorageService()
            file_bytes = await storage_service.download_object_bytes(
                FileUpDownRequest(bucket_name=data.bucket_name, object_key=document.file_key)
            )
            _set_review_progress(
                user_id=user_id,
                document_id=document.id,
                phase="extracting",
                stage_id="text-extraction",
                stage_name="解析正文和 OCR",
                detail="正在提取 PDF/DOCX/TXT 正文；低文本扫描页会自动进入 OCR。",
                percent=34,
            )
            extraction = await DocumentExtractionService().extract_async(
                file_bytes,
                file_name=document.file_name or document.file_key,
                mime_type=document.mime_type or "",
                enable_ocr=data.enable_ocr,
            )
            document_text = extraction.text
            extraction_info = {
                "parser": extraction.parser,
                "page_count": extraction.page_count,
                "char_count": extraction.char_count,
                "warnings": extraction.warnings,
                "text_layer_pages": extraction.text_layer_pages,
                "low_text_pages": extraction.low_text_pages,
                "ocr_pages": extraction.ocr_pages,
            }
            _set_review_progress(
                user_id=user_id,
                document_id=document.id,
                phase="extracting",
                stage_id="text-extraction",
                stage_name="解析正文和 OCR",
                detail=(
                    f"已提取 {extraction_info.get('char_count', 0)} 字符"
                    f"，页数 {extraction_info.get('page_count') or '未知'}。"
                    " 正在进入法律审查。"
                ),
                percent=40,
                status="completed",
                extra={"extraction": extraction_info},
            )
            await documents_service.update(
                document.id,
                {
                    "extracted_text": document_text,
                    "extraction_metadata_json": _json_dumps(extraction_info),
                    "extraction_error": "",
                    "status": "analyzing",
                },
                user_id=user_id,
            )

        _set_review_progress(
            user_id=user_id,
            document_id=document.id,
            phase="analyzing",
            stage_id="review-start",
            stage_name="启动 Agent Team",
            detail="已获得文书正文，正在启动多阶段法律审查。",
            percent=42,
        )
        service = DeepReviewService(
            review_prompt_extension=await _active_review_prompt_extension(db),
            progress_callback=publish_progress,
        )
        report = await service.generate_deep_review(
            document_text=document_text,
            document_type=data.document_type or document.doc_type or "合同",
            user_role=data.user_role or document.user_role or "甲方",
            review_goal=data.review_goal,
            known_facts=data.known_facts or [],
            jurisdiction=data.jurisdiction,
        )
        report_id, review_id = await _persist_deep_report(
            db=db,
            user_id=user_id,
            document_id=document.id,
            report=report,
        )
        await EntitlementService(db).consume_report(user_id=user_id, user_role=user_role)
        _set_review_progress(
            user_id=user_id,
            document_id=document.id,
            phase="completed",
            stage_id="completed",
            stage_name="报告已生成",
            detail="风险矩阵、修改建议、法律依据和导出数据已完成。",
            percent=100,
            status="completed",
            extra={"report_id": report_id, "review_id": review_id},
        )
        await documents_service.update(
            document.id,
            {
                "status": "completed",
                "extraction_error": "",
            },
            user_id=user_id,
        )
        return AnalyzeUploadedDocumentResponse(
            success=True,
            report_id=report_id,
            review_id=review_id,
            report=report,
            extraction=extraction_info,
        )
    except HTTPException:
        raise
    except DocumentExtractionError as e:
        _set_review_progress(
            user_id=user_id,
            document_id=document.id,
            phase="failed",
            stage_id="failed",
            stage_name="解析失败",
            detail=str(e),
            percent=100,
            status="error",
        )
        await documents_service.update(
            document.id,
            {"status": "failed", "extraction_error": str(e)},
            user_id=user_id,
        )
        return AnalyzeUploadedDocumentResponse(success=False, error=str(e), extraction=extraction_info)
    except ValueError as e:
        _set_review_progress(
            user_id=user_id,
            document_id=document.id,
            phase="failed",
            stage_id="failed",
            stage_name="审查失败",
            detail=str(e),
            percent=100,
            status="error",
        )
        await documents_service.update(
            document.id,
            {"status": "failed", "extraction_error": str(e)},
            user_id=user_id,
        )
        return AnalyzeUploadedDocumentResponse(success=False, error=str(e), extraction=extraction_info)
    except Exception as e:
        logger.error("Uploaded document deep review failed: %s", e, exc_info=True)
        _set_review_progress(
            user_id=user_id,
            document_id=document.id,
            phase="failed",
            stage_id="failed",
            stage_name="审查失败",
            detail=f"上传文书深度审查失败：{str(e)}",
            percent=100,
            status="error",
        )
        await documents_service.update(
            document.id,
            {"status": "failed", "extraction_error": str(e)},
            user_id=user_id,
        )
        return AnalyzeUploadedDocumentResponse(
            success=False,
            error=f"上传文书深度审查失败，请稍后重试。错误: {str(e)}",
            extraction=extraction_info,
        )


async def _run_uploaded_document_review_background(data_dict: Dict[str, Any], user_id: str, user_role: str) -> None:
    if not db_manager.async_session_maker:
        await db_manager.ensure_initialized()
    if not db_manager.async_session_maker:
        logger.error("Cannot start background deep review: database session maker unavailable")
        return

    data = AnalyzeUploadedDocumentRequest(**data_dict)
    async with db_manager.async_session_maker() as session:
        documents_service = DocumentsService(session)
        document = await documents_service.get_by_id(data.document_id, user_id=user_id)
        if not document:
            logger.warning("Background deep review skipped: document %s not found", data.document_id)
            return
        result = await _run_uploaded_document_review(
            db=session,
            document=document,
            data=data,
            user_id=user_id,
            user_role=user_role,
        )
        if not result.success:
            logger.warning("Background deep review failed for document %s: %s", data.document_id, result.error)


# ----------------- Endpoints -----------------

@router.post("/analyze", response_model=DeepReviewResponse)
async def analyze_document(
    data: DeepReviewRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a deep legal review report for the given document.
    Uses the configured OpenAI-compatible review model with the full Agent Team system prompt.
    """
    if not data.document_text or len(data.document_text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="文书内容过短，请提供完整的法律文书文本（至少50字）。"
        )

    try:
        entitlement_service = EntitlementService(db)
        await entitlement_service.assert_can_create_report(str(current_user.id), current_user.role)
        service = DeepReviewService(review_prompt_extension=await _active_review_prompt_extension(db))
        report = await service.generate_deep_review(
            document_text=data.document_text,
            document_type=data.document_type,
            user_role=data.user_role,
            review_goal=data.review_goal,
            known_facts=data.known_facts,
            jurisdiction=data.jurisdiction,
        )
        await entitlement_service.consume_report(str(current_user.id), current_user.role)
        return DeepReviewResponse(success=True, report=report)
    except ValueError as e:
        logger.warning(f"Review validation error: {e}")
        return DeepReviewResponse(success=False, error=str(e))
    except Exception as e:
        logger.error(f"Deep review failed: {e}")
        return DeepReviewResponse(
            success=False,
            error=f"审查报告生成失败，请稍后重试。错误: {str(e)}"
        )


@router.post("/analyze-uploaded", response_model=AnalyzeUploadedDocumentResponse)
async def analyze_uploaded_document(
    data: AnalyzeUploadedDocumentRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    End-to-end deep review for an uploaded document:
    fetch object storage file -> extract text -> run staged review pipeline -> persist full report.
    """
    documents_service = DocumentsService(db)
    document = await documents_service.get_by_id(data.document_id, user_id=str(current_user.id))
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    await EntitlementService(db).assert_can_create_report(str(current_user.id), current_user.role)
    return await _run_uploaded_document_review(
        db=db,
        document=document,
        data=data,
        user_id=str(current_user.id),
        user_role=current_user.role,
    )


@router.post("/analyze-uploaded/start", response_model=AnalyzeUploadedDocumentStartResponse)
async def start_uploaded_document_analysis(
    data: AnalyzeUploadedDocumentRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start uploaded-document review as a background job so the UI can poll progress."""
    documents_service = DocumentsService(db)
    document = await documents_service.get_by_id(data.document_id, user_id=str(current_user.id))
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    current_status = document.status or "processing"
    if current_status in {"queued", "extracting", "analyzing"}:
        return AnalyzeUploadedDocumentStartResponse(
            success=True,
            document_id=document.id,
            status=current_status,
            message=_status_message(current_status),
        )

    await EntitlementService(db).assert_can_create_report(str(current_user.id), current_user.role)
    await documents_service.update(
        document.id,
        {
            "status": "queued",
            "extraction_error": "",
        },
        user_id=str(current_user.id),
    )
    background_tasks.add_task(
        _run_uploaded_document_review_background,
        data.model_dump(),
        str(current_user.id),
        current_user.role,
    )
    return AnalyzeUploadedDocumentStartResponse(
        success=True,
        document_id=document.id,
        status="queued",
        message=_status_message("queued"),
    )


@router.get("/analyze-uploaded/status/{document_id}", response_model=AnalyzeUploadedDocumentStatusResponse)
async def get_uploaded_document_analysis_status(
    document_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return current uploaded-document review status for polling UIs."""
    user_id = str(current_user.id)
    documents_service = DocumentsService(db)
    document = await documents_service.get_by_id(document_id, user_id=user_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    status = document.status or "processing"
    extraction = _parse_extraction_info(document.extraction_metadata_json)
    report_id: Optional[int] = None
    review_id: Optional[int] = None
    progress = _get_review_progress(user_id, document_id, status)
    pipeline_preview: list[dict[str, Any]] = list(progress.get("completed_stages") or [])

    if status == "completed":
        report_result = await Review_reportsService(db).get_list(
            skip=0,
            limit=1,
            user_id=user_id,
            query_dict={"document_id": document_id},
            sort="-id",
        )
        reports = report_result.get("items", [])
        if reports:
            report_id = reports[0].id
            review_id = report_id
            trace = _json_loads_or(reports[0].pipeline_trace_json, [])
            if isinstance(trace, list) and trace:
                pipeline_preview = [
                    {
                        "stage_id": item.get("stage_id"),
                        "stage_name": item.get("stage_name"),
                        "status": item.get("status"),
                        "duration_ms": item.get("duration_ms"),
                    }
                    for item in trace
                    if isinstance(item, dict)
                ][-12:]

    return AnalyzeUploadedDocumentStatusResponse(
        success=True,
        document_id=document_id,
        status=status,
        report_id=report_id,
        review_id=review_id,
        extraction=extraction or None,
        progress=progress,
        pipeline_preview=pipeline_preview,
        error=document.extraction_error or None,
        message=_status_message(status),
    )


@router.get("/reports/by-document/{document_id}")
async def get_latest_deep_review_report_by_document(
    document_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the latest review_reports record for a document. This replaces legacy reviews/risk_items reads."""
    documents_service = DocumentsService(db)
    document = await documents_service.get_by_id(document_id, user_id=str(current_user.id))
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    result = await Review_reportsService(db).get_list(
        skip=0,
        limit=1,
        user_id=str(current_user.id),
        query_dict={"document_id": document_id},
        sort="-id",
    )
    reports = result.get("items", [])
    if not reports:
        raise HTTPException(status_code=404, detail="Deep review report not found")
    return _report_payload_from_record(reports[0])


@router.get("/pipeline/latest")
async def get_latest_pipeline_trace(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the latest persisted AI pipeline trace for the current user."""
    result = await Review_reportsService(db).get_list(
        skip=0,
        limit=1,
        user_id=str(current_user.id),
        sort="-id",
    )
    reports = result.get("items", [])
    if not reports:
        return {
            "success": True,
            "report_id": None,
            "document_id": None,
            "status": "empty",
            "generated_at": None,
            "total_duration_ms": 0,
            "trace": [],
        }
    return _pipeline_payload_from_record(reports[0])


@router.get("/reports/{report_id}/pipeline")
async def get_deep_review_report_pipeline(
    report_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stored = await Review_reportsService(db).get_by_id(report_id, user_id=str(current_user.id))
    if not stored:
        raise HTTPException(status_code=404, detail="Deep review report not found")
    return _pipeline_payload_from_record(stored)


@router.patch("/reports/{report_id}/paid")
async def mark_deep_review_report_paid(
    report_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stored = await Review_reportsService(db).update(
        report_id,
        {"is_paid": True},
        user_id=str(current_user.id),
    )
    if not stored:
        raise HTTPException(status_code=404, detail="Deep review report not found")
    return {"success": True, "report_id": stored.id, "review_id": stored.id, "is_paid": bool(stored.is_paid)}


@router.get("/reports/{report_id}", response_model=DeepReviewResponse)
async def get_deep_review_report(
    report_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report_service = Review_reportsService(db)
    stored = await report_service.get_by_id(report_id, user_id=str(current_user.id))
    if not stored:
        raise HTTPException(status_code=404, detail="Deep review report not found")
    if not stored.full_report_json:
        raise HTTPException(status_code=404, detail="Stored report does not contain full deep review JSON")
    try:
        report = json.loads(stored.full_report_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Stored report JSON is corrupted") from exc
    report = DeepReviewService().prepare_report_for_display(report)
    return DeepReviewResponse(success=True, report=report)


@router.get("/reports/{report_id}/export/{file_format}")
async def export_deep_review_report(
    report_id: int,
    file_format: str,
    current_user: UserResponse = Depends(get_export_user),
    db: AsyncSession = Depends(get_db),
):
    report_service = Review_reportsService(db)
    stored = await report_service.get_by_id(report_id, user_id=str(current_user.id))
    if not stored or not stored.full_report_json:
        raise HTTPException(status_code=404, detail="Deep review report not found")
    try:
        report = json.loads(stored.full_report_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Stored report JSON is corrupted") from exc

    report = DeepReviewService().prepare_report_for_display(report)
    meta = report.get("report_meta") or {}
    base_name = _safe_filename(meta.get("report_id") or f"deep-review-{report_id}")
    fmt = file_format.lower()

    if fmt in {"md", "markdown"}:
        content = _report_to_markdown(report).encode("utf-8-sig")
        return Response(
            content=content,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.md"'},
        )
    if fmt in {"doc", "word"}:
        content = _report_to_doc_html(report).encode("utf-8-sig")
        return Response(
            content=content,
            media_type="application/msword",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.doc"'},
        )
    if fmt == "json":
        content = json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8-sig")
        return Response(
            content=content,
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.json"'},
        )
    if fmt == "pdf":
        content = _report_to_pdf_bytes(report)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.pdf"'},
        )

    raise HTTPException(status_code=400, detail="Unsupported export format. Use pdf, doc, md, or json.")


@router.post("/generate-document", response_model=GenerateDocumentResponse)
async def generate_document(
    data: GenerateDocumentRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a legal document using AI from first principles.
    """
    if not data.doc_type:
        raise HTTPException(status_code=400, detail="请指定文书类型。")

    try:
        service = DeepReviewService()
        document = await service.generate_legal_document(
            doc_type=data.doc_type,
            user_role=data.user_role,
            title=data.title,
            input_data=data.input_data,
            language=data.language,
        )
        return GenerateDocumentResponse(success=True, document=document)
    except ValueError as e:
        logger.warning(f"Document generation validation error: {e}")
        return GenerateDocumentResponse(success=False, error=str(e))
    except Exception as e:
        logger.error(f"Document generation failed: {e}")
        return GenerateDocumentResponse(
            success=False,
            error=f"文书生成失败，请稍后重试。错误: {str(e)}"
        )


@router.post("/case-chat", response_model=CaseAIChatResponse)
async def case_ai_chat(
    data: CaseAIChatRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI chat for case workspace - provides legal analysis and assistance.
    """
    if not data.user_message:
        raise HTTPException(status_code=400, detail="请输入您的问题。")

    try:
        service = DeepReviewService()
        response = await service.generate_case_ai_response(
            case_context=data.case_context,
            user_message=data.user_message,
            conversation_history=data.conversation_history,
        )
        return CaseAIChatResponse(success=True, response=response)
    except Exception as e:
        logger.error(f"Case AI chat failed: {e}")
        return CaseAIChatResponse(
            success=False,
            error=f"AI助手响应失败，请稍后重试。"
        )
