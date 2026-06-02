from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.case_materials import Case_materialsService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/case_materials", tags=["case_materials"])


# ---------- Pydantic Schemas ----------
class Case_materialsData(BaseModel):
    """Entity data schema (for create/update)"""
    case_id: int
    material_no: str = None
    title: str
    material_type: str = None
    file_url: str = None
    parsed_text: str = None
    ocr_status: str = None
    source: str = None
    is_evidence: bool = None
    proof_purpose: str = None
    page_refs: str = None
    related_facts: str = None
    authenticity_status: str = None
    relevance_status: str = None
    legality_status: str = None
    admissibility_risk: str = None
    need_notarization: bool = None
    source_reliability: str = None


class Case_materialsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    case_id: Optional[int] = None
    material_no: Optional[str] = None
    title: Optional[str] = None
    material_type: Optional[str] = None
    file_url: Optional[str] = None
    parsed_text: Optional[str] = None
    ocr_status: Optional[str] = None
    source: Optional[str] = None
    is_evidence: Optional[bool] = None
    proof_purpose: Optional[str] = None
    page_refs: Optional[str] = None
    related_facts: Optional[str] = None
    authenticity_status: Optional[str] = None
    relevance_status: Optional[str] = None
    legality_status: Optional[str] = None
    admissibility_risk: Optional[str] = None
    need_notarization: Optional[bool] = None
    source_reliability: Optional[str] = None


class Case_materialsResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    case_id: int
    material_no: Optional[str] = None
    title: str
    material_type: Optional[str] = None
    file_url: Optional[str] = None
    parsed_text: Optional[str] = None
    ocr_status: Optional[str] = None
    source: Optional[str] = None
    is_evidence: Optional[bool] = None
    proof_purpose: Optional[str] = None
    page_refs: Optional[str] = None
    related_facts: Optional[str] = None
    authenticity_status: Optional[str] = None
    relevance_status: Optional[str] = None
    legality_status: Optional[str] = None
    admissibility_risk: Optional[str] = None
    need_notarization: Optional[bool] = None
    source_reliability: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Case_materialsListResponse(BaseModel):
    """List response schema"""
    items: List[Case_materialsResponse]
    total: int
    skip: int
    limit: int


class Case_materialsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Case_materialsData]


class Case_materialsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Case_materialsUpdateData


class Case_materialsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Case_materialsBatchUpdateItem]


class Case_materialsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Case_materialsListResponse)
async def query_case_materialss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query case_materialss with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying case_materialss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Case_materialsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} case_materialss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying case_materialss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Case_materialsListResponse)
async def query_case_materialss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query case_materialss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying case_materialss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Case_materialsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} case_materialss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying case_materialss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Case_materialsResponse)
async def get_case_materials(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single case_materials by ID (user can only see their own records)"""
    logger.debug(f"Fetching case_materials with id: {id}, fields={fields}")
    
    service = Case_materialsService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Case_materials with id {id} not found")
            raise HTTPException(status_code=404, detail="Case_materials not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching case_materials {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Case_materialsResponse, status_code=201)
async def create_case_materials(
    data: Case_materialsData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new case_materials"""
    logger.debug(f"Creating new case_materials with data: {data}")
    
    service = Case_materialsService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create case_materials")
        
        logger.info(f"Case_materials created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating case_materials: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating case_materials: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Case_materialsResponse], status_code=201)
async def create_case_materialss_batch(
    request: Case_materialsBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple case_materialss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} case_materialss")
    
    service = Case_materialsService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} case_materialss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Case_materialsResponse])
async def update_case_materialss_batch(
    request: Case_materialsBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple case_materialss in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} case_materialss")
    
    service = Case_materialsService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} case_materialss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Case_materialsResponse)
async def update_case_materials(
    id: int,
    data: Case_materialsUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing case_materials (requires ownership)"""
    logger.debug(f"Updating case_materials {id} with data: {data}")

    service = Case_materialsService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Case_materials with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Case_materials not found")
        
        logger.info(f"Case_materials {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating case_materials {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating case_materials {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_case_materialss_batch(
    request: Case_materialsBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple case_materialss by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} case_materialss")
    
    service = Case_materialsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} case_materialss successfully")
        return {"message": f"Successfully deleted {deleted_count} case_materialss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_case_materials(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single case_materials by ID (requires ownership)"""
    logger.debug(f"Deleting case_materials with id: {id}")
    
    service = Case_materialsService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Case_materials with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Case_materials not found")
        
        logger.info(f"Case_materials {id} deleted successfully")
        return {"message": "Case_materials deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting case_materials {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


