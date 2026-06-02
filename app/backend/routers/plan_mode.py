from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.auth import UserResponse
from services.plan_mode import PlanModeService

router = APIRouter(prefix="/api/v1/plan-mode", tags=["plan-mode"])


class PlanSessionCreateRequest(BaseModel):
    task_type: str = "auto"
    case_id: Optional[int] = None
    user_input: str = ""
    document_type: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)


class PlanAnswersRequest(BaseModel):
    answers: list[dict[str, Any]] = Field(default_factory=list)


class PlanGenerateRequest(BaseModel):
    approval: bool = True
    generation_mode: str = "draft"
    output_format: str = "markdown"


@router.post("/session")
async def create_plan_session(
    request: PlanSessionCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanModeService(db)
    try:
        session = await service.create_session(
            user_id=str(current_user.id),
            task_type=request.task_type,
            user_input=request.user_input,
            document_type=request.document_type,
            case_id=request.case_id,
            context=request.context,
        )
        return service.serialize(session)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Plan Mode 创建失败：{exc}")


@router.post("/session/{session_id}/answers")
async def submit_plan_answers(
    session_id: int,
    request: PlanAnswersRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanModeService(db)
    try:
        session = await service.add_answers(
            session_id=session_id,
            user_id=str(current_user.id),
            answers=request.answers,
        )
        return service.serialize(session)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/session/{session_id}/plan")
async def get_plan(
    session_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanModeService(db)
    try:
        session = await service.get_owned_session(session_id, str(current_user.id))
        return service.serialize(session)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/session/{session_id}/generate")
async def generate_from_plan(
    session_id: int,
    request: PlanGenerateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanModeService(db)
    try:
        session = await service.get_owned_session(session_id, str(current_user.id))
        if not request.approval:
            return {"success": False, "message": "用户未确认生成计划"}
        draft = service.generate_assumption_draft(session)
        return {"success": True, "session": service.serialize(session), "draft": draft}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
