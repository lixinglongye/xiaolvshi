import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_admin_user
from models.audit_logs import Audit_logs
from models.auth import User
from models.deletion_requests import Deletion_requests
from models.documents import Documents
from models.evaluation_cases import Evaluation_cases
from models.evaluation_runs import Evaluation_runs
from models.feedback_tickets import Feedback_tickets
from models.orders import Orders
from models.organization_members import Organization_members
from models.organizations import Organizations
from models.prompt_versions import Prompt_versions
from models.review_reports import Review_reports
from models.templates import Templates
from schemas.auth import UserResponse
from services.deep_review import DeepReviewService
from services.entitlements import EntitlementService, PLAN_LIMITS
from services.feedback_capture_plan import FeedbackCapturePlanService

router = APIRouter(prefix="/api/v1/admin/ops", tags=["admin-ops"])


class RoleUpdate(BaseModel):
    role: str


class SubscriptionUpdate(BaseModel):
    plan_type: str
    status: str = "active"


class StatusUpdate(BaseModel):
    status: Optional[str] = None
    operator_note: Optional[str] = None


class ReportUpdate(BaseModel):
    status: Optional[str] = None
    is_paid: Optional[bool] = None


class TemplateCreate(BaseModel):
    doc_type: str
    title: str
    content: Optional[str] = None
    is_active: bool = True
    language: str = "zh"


class TemplateUpdate(BaseModel):
    doc_type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None
    language: Optional[str] = None


class PromptVersionCreate(BaseModel):
    name: str
    purpose: str = "deep_review"
    version: str
    system_prompt: str
    user_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    status: str = "draft"
    is_active: bool = False
    notes: Optional[str] = None


class PromptVersionUpdate(BaseModel):
    name: Optional[str] = None
    purpose: Optional[str] = None
    version: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class EvaluationCaseCreate(BaseModel):
    title: str
    document_type: str = "合同"
    user_role: str = "甲方"
    input_text: str
    expected_risks_json: Optional[str] = None
    expected_sources_json: Optional[str] = None
    tags: Optional[str] = None
    status: str = "active"


class EvaluationCaseUpdate(BaseModel):
    title: Optional[str] = None
    document_type: Optional[str] = None
    user_role: Optional[str] = None
    input_text: Optional[str] = None
    expected_risks_json: Optional[str] = None
    expected_sources_json: Optional[str] = None
    tags: Optional[str] = None
    status: Optional[str] = None


class EvaluationRunRequest(BaseModel):
    prompt_version_id: Optional[int] = None
    case_ids: Optional[List[int]] = None
    limit: int = 3


def _row(obj: Any) -> Dict[str, Any]:
    return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}


def _apply_fields(obj: Any, values: Dict[str, Any]) -> None:
    for key, value in values.items():
        if value is not None and hasattr(obj, key) and key != "user_id":
            setattr(obj, key, value)


async def _count(db: AsyncSession, model: Any) -> int:
    result = await db.execute(select(func.count(getattr(model, "id"))))
    return int(result.scalar() or 0)


async def _list_model(
    db: AsyncSession,
    model: Any,
    *,
    skip: int = 0,
    limit: int = 100,
    sort: str = "-created_at",
) -> Dict[str, Any]:
    total = await _count(db, model)
    query = select(model)
    desc = sort.startswith("-")
    field_name = sort[1:] if desc else sort
    sort_col = getattr(model, field_name, getattr(model, "id"))
    query = query.order_by(sort_col.desc() if desc else sort_col.asc())
    result = await db.execute(query.offset(skip).limit(limit))
    return {
        "items": [_row(item) for item in result.scalars().all()],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


def _json_list(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        if isinstance(value, list):
            return [str(item.get("title") if isinstance(item, dict) else item) for item in value]
        if isinstance(value, dict):
            return [str(v) for v in value.values()]
    except json.JSONDecodeError:
        return [part.strip() for part in raw.split(",") if part.strip()]
    return []


def _prompt_extension(prompt: Optional[Prompt_versions]) -> str:
    if not prompt:
        return ""
    parts = [
        f"版本名称：{prompt.name}",
        f"版本号：{prompt.version}",
        "系统 Prompt：",
        prompt.system_prompt,
    ]
    if prompt.user_prompt:
        parts.extend(["用户 Prompt 补充：", prompt.user_prompt])
    return "\n".join(parts)


async def _audit(
    db: AsyncSession,
    *,
    admin_user_id: str,
    action: str,
    target_type: str,
    target_id: Any,
    detail: str = "",
) -> None:
    db.add(
        Audit_logs(
            user_id=admin_user_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            detail=detail[:2000],
        )
    )


@router.get("/overview")
async def overview(
    _admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return {
        "users": await _count(db, User),
        "orders": await _count(db, Orders),
        "reports": await _count(db, Review_reports),
        "documents": await _count(db, Documents),
        "templates": await _count(db, Templates),
        "prompt_versions": await _count(db, Prompt_versions),
        "evaluation_cases": await _count(db, Evaluation_cases),
        "evaluation_runs": await _count(db, Evaluation_runs),
        "feedback_open": await _filtered_count(db, Feedback_tickets, Feedback_tickets.status, ["open", "pending", None]),
        "deletion_pending": await _filtered_count(db, Deletion_requests, Deletion_requests.status, ["pending", None]),
    }


async def _filtered_count(db: AsyncSession, model: Any, column: Any, values: List[Any]) -> int:
    conditions = [column == value for value in values if value is not None]
    if any(value is None for value in values):
        conditions.append(column.is_(None))
    query = select(func.count(getattr(model, "id")))
    if conditions:
        from sqlalchemy import or_

        query = query.where(or_(*conditions))
    result = await db.execute(query)
    return int(result.scalar() or 0)


@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()).offset(skip).limit(limit))
    users = result.scalars().all()
    items = []
    entitlement_service = EntitlementService(db)
    for user in users:
        summary = await entitlement_service.get_entitlement_summary(user.id, user.role)
        item = _row(user)
        item["subscription"] = summary
        items.append(item)
    return {"items": items, "total": await _count(db, User), "skip": skip, "limit": limit}


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    data: RoleUpdate,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    if data.role not in {"user", "admin"}:
        raise HTTPException(status_code=400, detail="role must be user or admin")
    if user_id == admin.id and data.role != "admin":
        raise HTTPException(status_code=400, detail="Cannot remove your own admin role")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = data.role
    await _audit(db, admin_user_id=admin.id, action="admin_update_user_role", target_type="user", target_id=user_id)
    await db.commit()
    await db.refresh(user)
    return _row(user)


@router.put("/users/{user_id}/subscription")
async def update_user_subscription(
    user_id: str,
    data: SubscriptionUpdate,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    if data.plan_type not in PLAN_LIMITS:
        raise HTTPException(status_code=400, detail=f"plan_type must be one of {list(PLAN_LIMITS)}")
    subscription = await EntitlementService(db).upsert_subscription(
        user_id=user_id,
        plan_type=data.plan_type,
        status=data.status,
    )
    await _audit(
        db,
        admin_user_id=admin.id,
        action="admin_update_subscription",
        target_type="subscription",
        target_id=subscription.id,
        detail=json.dumps({"user_id": user_id, "plan_type": data.plan_type, "status": data.status}, ensure_ascii=False),
    )
    await db.commit()
    return _row(subscription)


@router.get("/orders")
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await _list_model(db, Orders, skip=skip, limit=limit)


@router.patch("/orders/{order_id}")
async def update_order(
    order_id: int,
    data: StatusUpdate,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    order = await db.get(Orders, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if data.status:
        order.status = data.status
    await _audit(db, admin_user_id=admin.id, action="admin_update_order", target_type="order", target_id=order_id)
    await db.commit()
    await db.refresh(order)
    return _row(order)


@router.get("/reports")
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await _list_model(db, Review_reports, skip=skip, limit=limit)


@router.patch("/reports/{report_id}")
async def update_report(
    report_id: int,
    data: ReportUpdate,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    report = await db.get(Review_reports, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if data.status is not None:
        report.status = data.status
    if data.is_paid is not None:
        report.is_paid = data.is_paid
    await _audit(db, admin_user_id=admin.id, action="admin_update_report", target_type="report", target_id=report_id)
    await db.commit()
    await db.refresh(report)
    return _row(report)


@router.get("/templates")
async def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await _list_model(db, Templates, skip=skip, limit=limit)


@router.post("/templates")
async def create_template(
    data: TemplateCreate,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    template = Templates(**data.model_dump())
    db.add(template)
    await _audit(db, admin_user_id=admin.id, action="admin_create_template", target_type="template", target_id="new")
    await db.commit()
    await db.refresh(template)
    return _row(template)


@router.patch("/templates/{template_id}")
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    template = await db.get(Templates, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    _apply_fields(template, data.model_dump())
    await _audit(db, admin_user_id=admin.id, action="admin_update_template", target_type="template", target_id=template_id)
    await db.commit()
    await db.refresh(template)
    return _row(template)


@router.get("/prompt-versions")
async def list_prompt_versions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await _list_model(db, Prompt_versions, skip=skip, limit=limit)


@router.post("/prompt-versions/seed-default")
async def seed_default_prompt_version(
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await _count(db, Prompt_versions)
    if existing:
        return {"created": 0, "message": "Prompt versions already exist"}
    prompt = Prompt_versions(
        user_id=admin.id,
        name="深度法律审查交付 Prompt",
        purpose="deep_review",
        version="v1.0-default",
        system_prompt=(
            "你必须把 LLM chat 输出约束为法律审查 SaaS 交付物："
            "每个风险必须定位原文、说明法律关系、列出适用依据和适用理由、给出保守版/平衡版/底线版修改建议；"
            "缺少事实时列入待补事实，不得编造法条、案例、法院或案号；"
            "有利条款不得使用模板化默认理由，必须说明该条款如何改善当前用户立场；"
            "法律依据附录必须区分已校验、待核验和实务参考。"
        ),
        user_prompt="优先保证报告字段完整性、引用可复核性和律师复核可用性。",
        status="active",
        is_active=True,
        notes="系统默认种子版本，可在运营后台复制后迭代。",
    )
    db.add(prompt)
    await _audit(db, admin_user_id=admin.id, action="admin_seed_default_prompt", target_type="prompt_version", target_id="new")
    await db.commit()
    await db.refresh(prompt)
    return {"created": 1, "item": _row(prompt)}


@router.post("/prompt-versions")
async def create_prompt_version(
    data: PromptVersionCreate,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    prompt = Prompt_versions(user_id=admin.id, **data.model_dump())
    db.add(prompt)
    if data.is_active:
        await db.flush()
        await _deactivate_other_prompts(db, purpose=data.purpose, keep_id=prompt.id)
        prompt.is_active = True
    await _audit(db, admin_user_id=admin.id, action="admin_create_prompt", target_type="prompt_version", target_id="new")
    await db.commit()
    await db.refresh(prompt)
    return _row(prompt)


@router.patch("/prompt-versions/{prompt_id}")
async def update_prompt_version(
    prompt_id: int,
    data: PromptVersionUpdate,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    prompt = await db.get(Prompt_versions, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    _apply_fields(prompt, data.model_dump())
    if data.is_active:
        await _deactivate_other_prompts(db, purpose=prompt.purpose, keep_id=prompt.id)
    await _audit(db, admin_user_id=admin.id, action="admin_update_prompt", target_type="prompt_version", target_id=prompt_id)
    await db.commit()
    await db.refresh(prompt)
    return _row(prompt)


@router.post("/prompt-versions/{prompt_id}/activate")
async def activate_prompt_version(
    prompt_id: int,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    prompt = await db.get(Prompt_versions, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    await _deactivate_other_prompts(db, purpose=prompt.purpose, keep_id=prompt.id)
    prompt.is_active = True
    prompt.status = "active"
    await _audit(db, admin_user_id=admin.id, action="admin_activate_prompt", target_type="prompt_version", target_id=prompt_id)
    await db.commit()
    await db.refresh(prompt)
    return _row(prompt)


async def _deactivate_other_prompts(db: AsyncSession, *, purpose: str, keep_id: Optional[int]) -> None:
    result = await db.execute(select(Prompt_versions).where(Prompt_versions.purpose == purpose))
    for prompt in result.scalars().all():
        if keep_id is None or prompt.id != keep_id:
            prompt.is_active = False


def _with_feedback_capture_summary(row: Dict[str, Any], planner: FeedbackCapturePlanService) -> Dict[str, Any]:
    plan = planner.build_plan({**row, "state": _feedback_lifecycle_state(row.get("status"))})
    capture = plan.get("capture_summary") or {}
    roadmap = plan.get("roadmap_alignment") or {}
    lifecycle = plan.get("lifecycle") or {}
    row["capture_summary"] = {
        "priority": capture.get("priority"),
        "assignee": capture.get("assignee"),
        "linked_need_id": capture.get("linked_need_id"),
        "roadmap_alignment_status": capture.get("roadmap_alignment_status"),
        "release_gate_links": list(capture.get("release_gate_links") or [])[:5],
        "missing_required_fields": list(capture.get("missing_required_fields") or [])[:5],
        "high_risk": capture.get("high_risk") is True,
    }
    row["roadmap_summary"] = {
        "status": roadmap.get("status"),
        "top_need_id": roadmap.get("top_need_id"),
        "match_count": roadmap.get("match_count", 0),
    }
    row["lifecycle_summary"] = {
        "state": lifecycle.get("state"),
        "next_state": lifecycle.get("next_state"),
        "blocking_check_ids": list(lifecycle.get("current_transition_blocking_check_ids") or [])[:5],
        "required_actions": [_clip_text(action, 160) for action in list(lifecycle.get("required_actions") or [])[:3]],
    }
    return row


def _feedback_lifecycle_state(status: Any) -> str:
    normalized = str(status or "").strip().lower()
    if normalized in {"processing", "in_progress", "working"}:
        return "in_progress"
    if normalized in {"release_validation", "validating"}:
        return "release_validation"
    if normalized in {"customer_visible_resolution", "customer_update"}:
        return "customer_visible_resolution"
    if normalized in {"resolved", "closed", "done"}:
        return "closed"
    if normalized in {"linked_gap", "linked"}:
        return "linked_gap"
    return "triage"


def _clip_text(value: Any, limit: int) -> str:
    text = str(value or "")
    return text if len(text) <= limit else f"{text[: limit - 1]}..."


@router.get("/feedback")
async def list_feedback(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    payload = await _list_model(db, Feedback_tickets, skip=skip, limit=limit)
    planner = FeedbackCapturePlanService()
    payload["items"] = [_with_feedback_capture_summary(row, planner) for row in payload["items"]]
    return payload


@router.patch("/feedback/{ticket_id}")
async def update_feedback(
    ticket_id: int,
    data: StatusUpdate,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    ticket = await db.get(Feedback_tickets, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Feedback ticket not found")
    if data.status:
        ticket.status = data.status
    if data.operator_note:
        ticket.resolution_note = data.operator_note
    await _audit(db, admin_user_id=admin.id, action="admin_update_feedback", target_type="feedback", target_id=ticket_id)
    await db.commit()
    await db.refresh(ticket)
    return _row(ticket)


@router.get("/deletion-requests")
async def list_deletion_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await _list_model(db, Deletion_requests, skip=skip, limit=limit)


@router.patch("/deletion-requests/{request_id}")
async def process_deletion_request(
    request_id: int,
    data: StatusUpdate,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    deletion = await db.get(Deletion_requests, request_id)
    if not deletion:
        raise HTTPException(status_code=404, detail="Deletion request not found")
    if data.status:
        deletion.status = data.status
    deletion.operator_note = data.operator_note
    deletion.processed_by = admin.id
    deletion.processed_at = datetime.now()
    if data.status in {"approved", "completed", "deleted"}:
        document = await db.get(Documents, deletion.document_id)
        if document:
            document.status = "deleted"
    await _audit(
        db,
        admin_user_id=admin.id,
        action="admin_process_deletion",
        target_type="deletion_request",
        target_id=request_id,
        detail=json.dumps(data.model_dump(), ensure_ascii=False),
    )
    await db.commit()
    await db.refresh(deletion)
    return _row(deletion)


@router.get("/teams")
async def list_teams(
    _admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    orgs = await _list_model(db, Organizations, limit=500)
    members = await _list_model(db, Organization_members, limit=1000)
    return {"organizations": orgs["items"], "members": members["items"]}


@router.patch("/teams/members/{member_id}")
async def update_team_member(
    member_id: int,
    data: StatusUpdate,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    member = await db.get(Organization_members, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    if data.status:
        member.status = data.status
    if data.operator_note:
        member.role = data.operator_note
    await _audit(db, admin_user_id=admin.id, action="admin_update_team_member", target_type="team_member", target_id=member_id)
    await db.commit()
    await db.refresh(member)
    return _row(member)


@router.get("/evaluation-cases")
async def list_evaluation_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await _list_model(db, Evaluation_cases, skip=skip, limit=limit)


@router.post("/evaluation-cases")
async def create_evaluation_case(
    data: EvaluationCaseCreate,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    case = Evaluation_cases(user_id=admin.id, **data.model_dump())
    db.add(case)
    await _audit(db, admin_user_id=admin.id, action="admin_create_eval_case", target_type="evaluation_case", target_id="new")
    await db.commit()
    await db.refresh(case)
    return _row(case)


@router.patch("/evaluation-cases/{case_id}")
async def update_evaluation_case(
    case_id: int,
    data: EvaluationCaseUpdate,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(Evaluation_cases, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Evaluation case not found")
    _apply_fields(case, data.model_dump())
    await _audit(db, admin_user_id=admin.id, action="admin_update_eval_case", target_type="evaluation_case", target_id=case_id)
    await db.commit()
    await db.refresh(case)
    return _row(case)


@router.post("/evaluation-cases/seed-contracts")
async def seed_contract_evaluation_cases(
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await _count(db, Evaluation_cases)
    if existing:
        return {"created": 0, "message": "Evaluation cases already exist"}
    seeds = [
        {
            "title": "租赁合同押金和维修责任风险",
            "document_type": "租赁合同",
            "user_role": "承租方",
            "input_text": "房屋租赁合同。甲方出租房屋给乙方，押金两个月。租赁期内房屋及设施维修均由乙方承担。乙方提前退租押金不退。争议由甲方所在地法院管辖。",
            "expected_risks_json": json.dumps(["押金不退", "维修责任", "管辖", "提前退租"], ensure_ascii=False),
            "expected_sources_json": json.dumps(["民法典", "格式条款"], ensure_ascii=False),
            "tags": "合同,租赁,承租方",
        },
        {
            "title": "服务合同验收和违约责任缺失",
            "document_type": "服务合同",
            "user_role": "甲方",
            "input_text": "技术服务合同。乙方提供系统开发服务，甲方付款。合同未约定交付标准、验收期限、缺陷修复和逾期违约责任。",
            "expected_risks_json": json.dumps(["验收标准", "缺陷修复", "逾期违约", "付款节点"], ensure_ascii=False),
            "expected_sources_json": json.dumps(["民法典", "合同编"], ensure_ascii=False),
            "tags": "合同,服务,验收",
        },
        {
            "title": "买卖合同单方免责和质量异议风险",
            "document_type": "买卖合同",
            "user_role": "买方",
            "input_text": "买卖合同。卖方交付设备后买方应立即付款。卖方对设备质量不承担任何责任，买方收到货物三日未提出异议视为验收合格。",
            "expected_risks_json": json.dumps(["单方免责", "质量责任", "验收期限", "格式条款"], ensure_ascii=False),
            "expected_sources_json": json.dumps(["民法典", "买卖合同"], ensure_ascii=False),
            "tags": "合同,买卖,质量",
        },
    ]
    for seed in seeds:
        db.add(Evaluation_cases(user_id=admin.id, status="active", **seed))
    await _audit(db, admin_user_id=admin.id, action="admin_seed_eval_cases", target_type="evaluation_case", target_id="batch")
    await db.commit()
    return {"created": len(seeds)}


@router.get("/evaluation-runs")
async def list_evaluation_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await _list_model(db, Evaluation_runs, skip=skip, limit=limit)


@router.post("/evaluation-runs/run")
async def run_evaluations(
    data: EvaluationRunRequest,
    admin: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    prompt = await _resolve_prompt(db, data.prompt_version_id)
    if not prompt:
        raise HTTPException(status_code=400, detail="No prompt version available. Create and activate one first.")

    case_query = select(Evaluation_cases).where(Evaluation_cases.status != "disabled").order_by(Evaluation_cases.id.asc())
    if data.case_ids:
        case_query = case_query.where(Evaluation_cases.id.in_(data.case_ids[:10]))
    else:
        case_query = case_query.limit(max(1, min(data.limit, 5)))
    result = await db.execute(case_query)
    cases = result.scalars().all()
    if not cases:
        raise HTTPException(status_code=400, detail="No evaluation cases available")

    service = DeepReviewService(review_prompt_extension=_prompt_extension(prompt))
    run_rows = []
    for case in cases:
        expected_risks = _json_list(case.expected_risks_json)
        expected_sources = _json_list(case.expected_sources_json)
        try:
            report = await service.generate_deep_review(
                document_text=case.input_text,
                document_type=case.document_type or "合同",
                user_role=case.user_role or "甲方",
                review_goal="评测集回归测试",
                known_facts=[],
                jurisdiction="中国大陆",
            )
            report_text = json.dumps(report, ensure_ascii=False)
            matched_risks = [risk for risk in expected_risks if risk and risk in report_text]
            matched_sources = [source for source in expected_sources if source and source in report_text]
            risk_score = len(matched_risks) / max(1, len(expected_risks))
            source_score = len(matched_sources) / max(1, len(expected_sources)) if expected_sources else 1
            score = round((risk_score * 0.75 + source_score * 0.25) * 100, 2)
            payload = {
                "prompt_version": prompt.version,
                "expected_risks": expected_risks,
                "matched_risks": matched_risks,
                "missing_risks": [risk for risk in expected_risks if risk not in matched_risks],
                "expected_sources": expected_sources,
                "matched_sources": matched_sources,
                "report_meta": report.get("report_meta", {}),
                "quality_score": (report.get("coverage_audit") or {}).get("quality_score"),
            }
            run = Evaluation_runs(
                user_id=admin.id,
                prompt_version_id=prompt.id,
                evaluation_case_id=case.id,
                status="completed",
                score=score,
                result_json=json.dumps(payload, ensure_ascii=False),
            )
        except Exception as exc:
            run = Evaluation_runs(
                user_id=admin.id,
                prompt_version_id=prompt.id,
                evaluation_case_id=case.id,
                status="failed",
                score=0,
                result_json=json.dumps({"error": str(exc)}, ensure_ascii=False),
            )
        db.add(run)
        run_rows.append(run)

    all_scores = [run.score for run in run_rows if run.score is not None]
    if all_scores:
        prompt.eval_score = round(sum(all_scores) / len(all_scores), 2)
    await _audit(db, admin_user_id=admin.id, action="admin_run_eval", target_type="prompt_version", target_id=prompt.id)
    await db.commit()
    for run in run_rows:
        await db.refresh(run)
    return {
        "prompt_version_id": prompt.id,
        "average_score": prompt.eval_score,
        "items": [_row(run) for run in run_rows],
    }


async def _resolve_prompt(db: AsyncSession, prompt_version_id: Optional[int]) -> Optional[Prompt_versions]:
    if prompt_version_id:
        return await db.get(Prompt_versions, prompt_version_id)
    result = await db.execute(
        select(Prompt_versions)
        .where(Prompt_versions.purpose == "deep_review")
        .where(Prompt_versions.is_active.is_(True))
        .order_by(Prompt_versions.id.desc())
        .limit(1)
    )
    prompt = result.scalar_one_or_none()
    if prompt:
        return prompt
    result = await db.execute(select(Prompt_versions).order_by(Prompt_versions.id.desc()).limit(1))
    return result.scalar_one_or_none()
