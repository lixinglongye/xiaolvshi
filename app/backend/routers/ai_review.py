# @File: backend/routers/ai_review.py
# @Desc: Legacy AI routes kept only for compatibility redirects and document deletion.
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.auth import UserResponse
from services.audit_logs import Audit_logsService
from services.deletion_requests import Deletion_requestsService
from services.documents import DocumentsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["ai-review"])


DISCLAIMER_TEXT = (
    "本产品输出为 AI 辅助生成的风险提示和文书草稿，不构成正式法律意见；"
    "复杂事项请咨询执业律师。"
)


class ReviewCreateRequest(BaseModel):
    document_id: int


class GenerateDocumentRequest(BaseModel):
    doc_type: str
    user_role: Optional[str] = None
    title: Optional[str] = None
    input_data: Dict[str, Any] = {}
    language: Optional[str] = "zh"


class DeleteDocumentRequest(BaseModel):
    document_id: int
    reason: Optional[str] = ""


@router.post("/reviews/run")
async def run_review(
    data: ReviewCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deprecated mock review endpoint. Use /api/v1/deep-review/analyze-uploaded."""
    _ = (data, current_user, db)
    raise HTTPException(
        status_code=410,
        detail="该旧接口已停用，避免生成模拟审查结果。请改用 /api/v1/deep-review/analyze-uploaded。",
    )


@router.post("/generate_document")
async def generate_document(
    data: GenerateDocumentRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deprecated mock generation endpoint. Use /api/v1/deep-review/generate-document."""
    _ = (data, current_user, db)
    raise HTTPException(
        status_code=410,
        detail="该旧接口已停用，避免生成模板化文书。请改用 /api/v1/deep-review/generate-document。",
    )


@router.post("/documents/delete")
async def delete_document_with_audit(
    data: DeleteDocumentRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a document and record deletion request + audit log."""
    try:
        documents_service = DocumentsService(db)
        deletion_service = Deletion_requestsService(db)
        audit_service = Audit_logsService(db)

        document = await documents_service.get_by_id(data.document_id, user_id=current_user.id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        await documents_service.update(
            data.document_id,
            {"status": "deleted"},
            user_id=current_user.id,
        )
        await deletion_service.create(
            {
                "document_id": data.document_id,
                "reason": data.reason or "",
                "status": "processed",
            },
            user_id=current_user.id,
        )
        try:
            await audit_service.create(
                {
                    "action": "document_delete",
                    "target_type": "document",
                    "target_id": str(data.document_id),
                    "detail": json.dumps({"reason": data.reason or ""}, ensure_ascii=False),
                },
                user_id=current_user.id,
            )
        except Exception:
            pass
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_document error: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}") from e


@router.get("/disclaimer")
async def get_disclaimer():
    return {"disclaimer": DISCLAIMER_TEXT}
