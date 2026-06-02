from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.evidences import EvidencesService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/evidences", tags=["evidences"])


# ---------- Pydantic Schemas ----------
class EvidencesData(BaseModel):
    """Entity data schema (for create/update)"""
    case_id: int
    material_id: int = None
    evidence_no: str = None
    title: str
    evidence_type: str = None
    source: str = None
    proof_purpose: str = None
    related_fact_ids: str = None
    authenticity: str = None
    relevance: str = None
    legality: str = None
    risk_note: str = None
    need_reinforcement: bool = None
    status: str = None


class EvidencesUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    case_id: Optional[int] = None
    material_id: Optional[int] = None
    evidence_no: Optional[str] = None
    title: Optional[str] = None
    evidence_type: Optional[str] = None
    source: Optional[str] = None
    proof_purpose: Optional[str] = None
    related_fact_ids: Optional[str] = None
    authenticity: Optional[str] = None
    relevance: Optional[str] = None
    legality: Optional[str] = None
    risk_note: Optional[str] = None
    need_reinforcement: Optional[bool] = None
    status: Optional[str] = None


class EvidencesResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    case_id: int
    material_id: Optional[int] = None
    evidence_no: Optional[str] = None
    title: str
    evidence_type: Optional[str] = None
    source: Optional[str] = None
    proof_purpose: Optional[str] = None
    related_fact_ids: Optional[str] = None
    authenticity: Optional[str] = None
    relevance: Optional[str] = None
    legality: Optional[str] = None
    risk_note: Optional[str] = None
    need_reinforcement: Optional[bool] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EvidencesListResponse(BaseModel):
    """List response schema"""
    items: List[EvidencesResponse]
    total: int
    skip: int
    limit: int


class EvidencesBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[EvidencesData]


class EvidencesBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: EvidencesUpdateData


class EvidencesBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[EvidencesBatchUpdateItem]


class EvidencesBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=EvidencesListResponse)
async def query_evidencess(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query evidencess with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying evidencess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = EvidencesService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} evidencess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying evidencess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=EvidencesListResponse)
async def query_evidencess_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query evidencess with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying evidencess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = EvidencesService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} evidencess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying evidencess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=EvidencesResponse)
async def get_evidences(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single evidences by ID (user can only see their own records)"""
    logger.debug(f"Fetching evidences with id: {id}, fields={fields}")
    
    service = EvidencesService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Evidences with id {id} not found")
            raise HTTPException(status_code=404, detail="Evidences not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching evidences {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=EvidencesResponse, status_code=201)
async def create_evidences(
    data: EvidencesData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new evidences"""
    logger.debug(f"Creating new evidences with data: {data}")
    
    service = EvidencesService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create evidences")
        
        logger.info(f"Evidences created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating evidences: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating evidences: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[EvidencesResponse], status_code=201)
async def create_evidencess_batch(
    request: EvidencesBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple evidencess in a single request"""
    logger.debug(f"Batch creating {len(request.items)} evidencess")
    
    service = EvidencesService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} evidencess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[EvidencesResponse])
async def update_evidencess_batch(
    request: EvidencesBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple evidencess in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} evidencess")
    
    service = EvidencesService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} evidencess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=EvidencesResponse)
async def update_evidences(
    id: int,
    data: EvidencesUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing evidences (requires ownership)"""
    logger.debug(f"Updating evidences {id} with data: {data}")

    service = EvidencesService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Evidences with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Evidences not found")
        
        logger.info(f"Evidences {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating evidences {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating evidences {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_evidencess_batch(
    request: EvidencesBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple evidencess by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} evidencess")
    
    service = EvidencesService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} evidencess successfully")
        return {"message": f"Successfully deleted {deleted_count} evidencess", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_evidences(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single evidences by ID (requires ownership)"""
    logger.debug(f"Deleting evidences with id: {id}")
    
    service = EvidencesService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Evidences with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Evidences not found")
        
        logger.info(f"Evidences {id} deleted successfully")
        return {"message": "Evidences deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting evidences {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


