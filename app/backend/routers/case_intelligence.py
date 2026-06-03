from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.auth import UserResponse
from services.case_ai_workbench import CaseAIWorkbenchService
from services.case_intelligence import CaseDraftingService, CaseImportService

router = APIRouter(prefix="/api/v1/cases", tags=["case-intelligence"])


class ConfirmClustersRequest(BaseModel):
    clusters: list[dict[str, Any]] = Field(default_factory=list)


class GenerateEvidenceCatalogRequest(BaseModel):
    request_metadata: dict[str, Any] | None = None


class GenerateCivilComplaintRequest(BaseModel):
    force_draft: bool = True
    request_metadata: dict[str, Any] | None = None


class CaseAIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=6000)
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    request_metadata: dict[str, Any] | None = None


@router.post("/import-zip")
async def import_case_zip(
    file: UploadFile = File(...),
    upload_mode: str = Form("auto"),
    workspace_id: Optional[str] = Form(None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if upload_mode not in {"single_case", "multi_case", "auto"}:
        raise HTTPException(status_code=400, detail="upload_mode must be single_case, multi_case, or auto")
    if not (file.filename or "").lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="请上传 ZIP 案件材料包")
    data = await file.read()
    service = CaseImportService(db)
    try:
        return await service.import_zip(
            user_id=str(current_user.id),
            file_bytes=data,
            filename=file.filename or "case.zip",
            upload_mode=upload_mode,
            workspace_id=workspace_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"案件包导入失败：{exc}")


@router.get("/import-jobs/{job_id}")
async def get_import_job(
    job_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CaseImportService(db)
    try:
        job = await service.get_job(job_id=job_id, user_id=str(current_user.id))
        return await service.serialize_job(job, include_files=True)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/import-jobs/{job_id}/confirm-clusters")
async def confirm_import_clusters(
    job_id: int,
    request: ConfirmClustersRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CaseImportService(db)
    try:
        return await service.confirm_clusters(
            job_id=job_id,
            user_id=str(current_user.id),
            clusters=request.clusters,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/{case_id}/workspace")
async def get_case_workspace(
    case_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CaseDraftingService(db)
    try:
        workspace = await service.load_workspace(case_id, str(current_user.id))
        case = workspace["case"]
        return {
            "case": {
                "id": case.id,
                "title": case.title,
                "case_type": case.case_type,
                "stage": case.stage,
                "client_name": case.client_name,
                "opposing_party": case.opposing_party,
                "amount": case.amount,
                "summary": case.summary,
                "dispute_focus": case.dispute_focus,
                "claims": case.claims,
                "legal_basis": case.legal_basis,
                "missing_materials": case.missing_materials,
                "next_steps": case.next_steps,
            },
            "counts": {
                "materials": len(workspace["materials"]),
                "evidence_items": len(workspace["evidence_items"]),
                "facts": len(workspace["facts"]),
                "parties": len(workspace["parties"]),
                "claims": len(workspace["claims"]),
            },
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{case_id}/generate/evidence-catalog")
async def generate_evidence_catalog(
    case_id: int,
    request: GenerateEvidenceCatalogRequest = Body(default_factory=GenerateEvidenceCatalogRequest),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CaseDraftingService(db)
    try:
        return await service.generate_evidence_catalog(
            case_id=case_id,
            user_id=str(current_user.id),
            request_metadata=request.request_metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"证据目录生成失败：{exc}")


@router.post("/{case_id}/generate/civil-complaint")
async def generate_civil_complaint(
    case_id: int,
    request: GenerateCivilComplaintRequest = Body(default_factory=GenerateCivilComplaintRequest),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CaseDraftingService(db)
    try:
        return await service.generate_civil_complaint(
            case_id=case_id,
            user_id=str(current_user.id),
            force_draft=request.force_draft,
            request_metadata=request.request_metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"民事起诉状生成失败：{exc}")


@router.post("/{case_id}/ai-chat")
async def case_ai_chat(
    case_id: int,
    request: CaseAIChatRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CaseAIWorkbenchService(db)
    try:
        return await service.chat(
            case_id=case_id,
            user_id=str(current_user.id),
            message=request.message,
            conversation_history=request.conversation_history,
            request_metadata=request.request_metadata,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 503 if "AI service not configured" in detail else 404 if "Case not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"案件 AI 分析失败：{exc}")
