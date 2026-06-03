from routers.crud_helpers import parse_query_param, partial_update_data
import hashlib
import json
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.generated_documents import Generated_documents
from services.billing_entitlement_quota_binding import BillingEntitlementQuotaBindingService, build_quota_subject_hash
from services.generated_documents import Generated_documentsService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/generated_documents", tags=["generated_documents"])

GENERATED_DOCUMENT_QUOTA_SOURCE = "generated_documents.create"
GENERATED_DOCUMENT_QUOTA_UNITS = 1


# ---------- Pydantic Schemas ----------
class Generated_documentsData(BaseModel):
    """Entity data schema (for create/update)"""
    case_id: int = None
    doc_type: str
    user_role: str = None
    title: str = None
    content: str = None
    draft_label: str = None
    input_data_json: str = None
    citation_map: str = None
    status: str = None
    generated_by: str = None


class Generated_documentsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    case_id: Optional[int] = None
    doc_type: Optional[str] = None
    user_role: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    draft_label: Optional[str] = None
    input_data_json: Optional[str] = None
    citation_map: Optional[str] = None
    status: Optional[str] = None
    generated_by: Optional[str] = None


class Generated_documentsResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    case_id: Optional[int] = None
    doc_type: str
    user_role: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    draft_label: Optional[str] = None
    input_data_json: Optional[str] = None
    citation_map: Optional[str] = None
    status: Optional[str] = None
    generated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Generated_documentsListResponse(BaseModel):
    """List response schema"""
    items: List[Generated_documentsResponse]
    total: int
    skip: int
    limit: int


class Generated_documentsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Generated_documentsData]


class Generated_documentsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Generated_documentsUpdateData


class Generated_documentsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Generated_documentsBatchUpdateItem]


class Generated_documentsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


def _safe_document_log_fields(data: Generated_documentsData | Generated_documentsUpdateData) -> dict[str, object]:
    """Return non-content fields only; titles/content/input facts must not enter logs."""
    return {
        "case_id": data.case_id,
        "doc_type": data.doc_type,
        "status": data.status,
        "generated_by": data.generated_by,
    }


def _quota_event_id(
    data: Generated_documentsData,
    *,
    idempotency_key: str | None = None,
    batch_index: int | None = None,
) -> str:
    payload: dict[str, object] = {
        "schema": "generated_documents.create.v1",
        "payload": data.model_dump(),
    }
    if idempotency_key:
        payload["idempotency_key_hash"] = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
    if batch_index is not None:
        payload["batch_index"] = batch_index
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return f"generated_document_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:32]}"


def _quota_blocked_exception(summary: dict) -> HTTPException:
    usage_event = summary.get("last_usage_event") or {}
    return HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            "code": "report_quota_blocked",
            "decision_status": usage_event.get("decision_status") or summary.get("decision_status"),
            "reason_codes": summary.get("reason_codes") or usage_event.get("reason_codes") or [],
            "quota_window": summary.get("quota_window"),
            "reports_remaining": summary.get("reports_remaining"),
        },
    )


async def _consume_generated_document_quota(
    db: AsyncSession,
    *,
    current_user: UserResponse,
    data: Generated_documentsData,
    idempotency_key: str | None = None,
    batch_index: int | None = None,
) -> dict:
    summary = await BillingEntitlementQuotaBindingService(db).consume_report_usage(
        user_id=str(current_user.id),
        user_role=current_user.role,
        quota_subject_hash=build_quota_subject_hash(str(current_user.id)),
        source=GENERATED_DOCUMENT_QUOTA_SOURCE,
        event_id=_quota_event_id(data, idempotency_key=idempotency_key, batch_index=batch_index),
        units=GENERATED_DOCUMENT_QUOTA_UNITS,
    )
    usage_event = summary.get("last_usage_event") or {}
    if usage_event.get("decision_status") == "blocked":
        raise _quota_blocked_exception(summary)
    return summary


async def _preflight_generated_document_quota(
    db: AsyncSession,
    *,
    current_user: UserResponse,
    requested_units: int,
) -> dict | None:
    if requested_units <= 0:
        return None
    try:
        summary = await BillingEntitlementQuotaBindingService(db).build_entitlement_summary(
            user_id=str(current_user.id),
            user_role=current_user.role,
            quota_subject_hash=build_quota_subject_hash(str(current_user.id)),
            requested_units=requested_units,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not summary.get("can_create_report"):
        raise _quota_blocked_exception(summary)
    return summary


async def _find_existing_generated_document(
    db: AsyncSession,
    *,
    user_id: str,
    data: Generated_documentsData,
) -> Generated_documents | None:
    conditions = [Generated_documents.user_id == user_id]
    for field, value in data.model_dump().items():
        if not hasattr(Generated_documents, field):
            continue
        column = getattr(Generated_documents, field)
        conditions.append(column.is_(None) if value is None else column == value)

    result = await db.execute(
        select(Generated_documents)
        .where(*conditions)
        .order_by(Generated_documents.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ---------- Routes ----------
@router.get("", response_model=Generated_documentsListResponse)
async def query_generated_documentss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query generated_documentss with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying generated_documentss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Generated_documentsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} generated_documentss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying generated_documentss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Generated_documentsListResponse)
async def query_generated_documentss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query generated_documentss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying generated_documentss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Generated_documentsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} generated_documentss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying generated_documentss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Generated_documentsResponse)
async def get_generated_documents(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single generated_documents by ID (user can only see their own records)"""
    logger.debug(f"Fetching generated_documents with id: {id}, fields={fields}")
    
    service = Generated_documentsService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Generated_documents with id {id} not found")
            raise HTTPException(status_code=404, detail="Generated_documents not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching generated_documents {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Generated_documentsResponse, status_code=201)
async def create_generated_documents(
    data: Generated_documentsData,
    response: Response,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new generated_documents"""
    logger.debug("Creating new generated_documents with metadata: %s", _safe_document_log_fields(data))
    
    service = Generated_documentsService(db)
    try:
        quota_summary = await _consume_generated_document_quota(
            db,
            current_user=current_user,
            data=data,
            idempotency_key=idempotency_key,
        )
        usage_event = quota_summary.get("last_usage_event") or {}
        if usage_event.get("idempotent_replay"):
            existing = await _find_existing_generated_document(db, user_id=str(current_user.id), data=data)
            if existing:
                response.status_code = status.HTTP_200_OK
                return existing

        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create generated_documents")
        
        logger.info(f"Generated_documents created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating generated_documents: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating generated_documents: %s", type(e).__name__, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/batch", response_model=List[Generated_documentsResponse], status_code=201)
async def create_generated_documentss_batch(
    request: Generated_documentsBatchCreateRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple generated_documentss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} generated_documentss")
    
    service = Generated_documentsService(db)
    results = []
    
    try:
        existing_by_index: dict[int, Generated_documents] = {}
        for index, item_data in enumerate(request.items):
            existing = await _find_existing_generated_document(db, user_id=str(current_user.id), data=item_data)
            if existing:
                existing_by_index[index] = existing
        await _preflight_generated_document_quota(
            db,
            current_user=current_user,
            requested_units=len(request.items) - len(existing_by_index),
        )

        for index, item_data in enumerate(request.items):
            if index in existing_by_index:
                results.append(existing_by_index[index])
                continue

            quota_summary = await _consume_generated_document_quota(
                db,
                current_user=current_user,
                data=item_data,
                idempotency_key=idempotency_key,
                batch_index=index,
            )
            usage_event = quota_summary.get("last_usage_event") or {}
            if usage_event.get("idempotent_replay"):
                existing = await _find_existing_generated_document(db, user_id=str(current_user.id), data=item_data)
                if existing:
                    results.append(existing)
                    continue

            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} generated_documentss successfully")
        return results
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error in batch create: %s", type(e).__name__, exc_info=True)
        raise HTTPException(status_code=500, detail="Batch create failed")


@router.put("/batch", response_model=List[Generated_documentsResponse])
async def update_generated_documentss_batch(
    request: Generated_documentsBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple generated_documentss in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} generated_documentss")
    
    service = Generated_documentsService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} generated_documentss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Generated_documentsResponse)
async def update_generated_documents(
    id: int,
    data: Generated_documentsUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing generated_documents (requires ownership)"""
    logger.debug("Updating generated_documents %s with metadata: %s", id, _safe_document_log_fields(data))

    service = Generated_documentsService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Generated_documents with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Generated_documents not found")
        
        logger.info(f"Generated_documents {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating generated_documents {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating generated_documents {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_generated_documentss_batch(
    request: Generated_documentsBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple generated_documentss by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} generated_documentss")
    
    service = Generated_documentsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} generated_documentss successfully")
        return {"message": f"Successfully deleted {deleted_count} generated_documentss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_generated_documents(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single generated_documents by ID (requires ownership)"""
    logger.debug(f"Deleting generated_documents with id: {id}")
    
    service = Generated_documentsService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Generated_documents with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Generated_documents not found")
        
        logger.info(f"Generated_documents {id} deleted successfully")
        return {"message": "Generated_documents deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting generated_documents {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


