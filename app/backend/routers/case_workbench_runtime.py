from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.auth import UserResponse
from services.case_workbench_runtime_binding import CaseWorkbenchRuntimeBindingService


router = APIRouter(prefix="/api/v1/cases", tags=["case-workbench-runtime"])


def _normalize_event_binding(
    *,
    case_id: str,
    event: dict[str, Any],
    workspace_id: str | None = None,
    section: str | None = None,
) -> dict[str, Any]:
    normalized = dict(event)

    event_case_id = normalized.get("case_ref_hash")
    if event_case_id is None:
        normalized["case_ref_hash"] = case_id
    elif event_case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="case_id does not match event.case_ref_hash",
        )
    else:
        normalized["case_ref_hash"] = case_id

    if workspace_id is not None:
        event_workspace_id = normalized.get("matter_ref_hash")
        if event_workspace_id is not None and event_workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="workspace_id does not match event.matter_ref_hash",
            )
        normalized["matter_ref_hash"] = workspace_id

    if section is not None:
        event_section = normalized.get("section")
        if event_section is not None and event_section != section:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="section does not match event.section",
            )
        normalized["section"] = section

    return normalized


@router.get("/{case_id}/workbench/state")
async def get_case_workbench_state(
    case_id: str,
    workspace_id: str | None = Query(None),
    section: str | None = Query(None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CaseWorkbenchRuntimeBindingService()
    try:
        return await service.get_state_payload(
            db,
            user_id=str(current_user.id),
            case_id=case_id,
            workspace_id=workspace_id,
            sections=section,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid case workbench runtime request",
        )


@router.post("/{case_id}/workbench/state-events")
async def apply_case_workbench_state_event(
    case_id: str,
    event: dict[str, Any] = Body(...),
    workspace_id: str | None = Query(None),
    section: str | None = Query(None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CaseWorkbenchRuntimeBindingService()
    normalized_event = _normalize_event_binding(
        case_id=case_id,
        event=event,
        workspace_id=workspace_id,
        section=section,
    )
    try:
        return await service.apply_section_state_event(
            db,
            user_id=str(current_user.id),
            event=normalized_event,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid case workbench runtime request",
        )


@router.get("/{case_id}/workbench/state-events")
async def list_case_workbench_state_events(
    case_id: str,
    section: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CaseWorkbenchRuntimeBindingService()
    try:
        return await service.list_event_audit_trail(
            db,
            user_id=str(current_user.id),
            case_id=case_id,
            section=section,
            limit=limit,
            offset=offset,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid case workbench runtime request",
        )
