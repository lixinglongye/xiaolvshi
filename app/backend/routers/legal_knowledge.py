import logging
from typing import Optional

from core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.legal_knowledge import (
    LegalKnowledgeArticleResponse,
    LegalKnowledgeSearchResponse,
    LegalKnowledgeSeedResponse,
    LegalKnowledgeStatsResponse,
)
from services.legal_knowledge_audit import LegalKnowledgeAuditService
from services.legal_knowledge import LegalKnowledgeService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/legal-knowledge", tags=["legal_knowledge"])


@router.get("/search", response_model=LegalKnowledgeSearchResponse)
async def search_legal_knowledge(
    q: str = Query("", description="检索词，例如：违约金、格式条款、解除、租赁维修"),
    domain: Optional[str] = Query(None, description="法律领域，例如：合同审查"),
    topic: Optional[str] = Query(None, description="主题过滤，例如：违约责任"),
    source_type: Optional[str] = Query(None, description="来源类型，例如：法律、司法解释、指导案例"),
    authority_level: Optional[str] = Query(None, description="效力层级，例如：裁判依据、参考依据"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    service = LegalKnowledgeService(db)
    try:
        return await service.search(q, domain, topic, source_type, authority_level, limit)
    except Exception as exc:
        logger.error("Failed to search legal knowledge: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Legal knowledge search failed: {exc}")


@router.get("/sources/{source_id}", response_model=LegalKnowledgeArticleResponse)
async def get_legal_knowledge_source(source_id: str, db: AsyncSession = Depends(get_db)):
    service = LegalKnowledgeService(db)
    article = await service.get_by_source_id(source_id)
    if not article:
        raise HTTPException(status_code=404, detail="Legal knowledge source not found")
    return article


@router.get("/stats", response_model=LegalKnowledgeStatsResponse)
async def get_legal_knowledge_stats(db: AsyncSession = Depends(get_db)):
    service = LegalKnowledgeService(db)
    return await service.stats()


@router.get("/audit")
async def audit_legal_knowledge_seed(
    seed_path: Optional[str] = Query(None, description="可选 JSON seed 路径；默认读取内置合同审查 seed"),
):
    try:
        return {
            "success": True,
            "data": LegalKnowledgeAuditService().audit_seed_file(seed_path=seed_path),
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Seed file not found: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/admin/seed", response_model=LegalKnowledgeSeedResponse)
async def seed_legal_knowledge(
    seed_path: Optional[str] = Query(None, description="可选 JSON seed 路径；默认读取内置合同审查 seed"),
    dry_run: bool = Query(False, description="只计算差异，不写入数据库"),
    db: AsyncSession = Depends(get_db),
):
    service = LegalKnowledgeService(db)
    try:
        return await service.upsert_seed_records(seed_path=seed_path, dry_run=dry_run)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Seed file not found: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to seed legal knowledge: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Legal knowledge seed failed: {exc}")
