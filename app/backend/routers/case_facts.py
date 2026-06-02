from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.case_facts import Case_factsService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/case_facts", tags=["case_facts"])


# ---------- Pydantic Schemas ----------
class Case_factsData(BaseModel):
    """Entity data schema (for create/update)"""
    case_id: int
    fact_no: str = None
    event_date: str = None
    fact_text: str
    persons: str = None
    amount: str = None
    source_refs: str = None
    confidence: str = None
    verified_by_user: bool = None
    contradiction_note: str = None


class Case_factsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    case_id: Optional[int] = None
    fact_no: Optional[str] = None
    event_date: Optional[str] = None
    fact_text: Optional[str] = None
    persons: Optional[str] = None
    amount: Optional[str] = None
    source_refs: Optional[str] = None
    confidence: Optional[str] = None
    verified_by_user: Optional[bool] = None
    contradiction_note: Optional[str] = None


class Case_factsResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    case_id: int
    fact_no: Optional[str] = None
    event_date: Optional[str] = None
    fact_text: str
    persons: Optional[str] = None
    amount: Optional[str] = None
    source_refs: Optional[str] = None
    confidence: Optional[str] = None
    verified_by_user: Optional[bool] = None
    contradiction_note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Case_factsListResponse(BaseModel):
    """List response schema"""
    items: List[Case_factsResponse]
    total: int
    skip: int
    limit: int


class Case_factsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Case_factsData]


class Case_factsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Case_factsUpdateData


class Case_factsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Case_factsBatchUpdateItem]


class Case_factsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Case_factsListResponse)
async def query_case_factss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query case_factss with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying case_factss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Case_factsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} case_factss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying case_factss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Case_factsListResponse)
async def query_case_factss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query case_factss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying case_factss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Case_factsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} case_factss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying case_factss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Case_factsResponse)
async def get_case_facts(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single case_facts by ID (user can only see their own records)"""
    logger.debug(f"Fetching case_facts with id: {id}, fields={fields}")
    
    service = Case_factsService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Case_facts with id {id} not found")
            raise HTTPException(status_code=404, detail="Case_facts not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching case_facts {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Case_factsResponse, status_code=201)
async def create_case_facts(
    data: Case_factsData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new case_facts"""
    logger.debug(f"Creating new case_facts with data: {data}")
    
    service = Case_factsService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create case_facts")
        
        logger.info(f"Case_facts created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating case_facts: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating case_facts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Case_factsResponse], status_code=201)
async def create_case_factss_batch(
    request: Case_factsBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple case_factss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} case_factss")
    
    service = Case_factsService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} case_factss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Case_factsResponse])
async def update_case_factss_batch(
    request: Case_factsBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple case_factss in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} case_factss")
    
    service = Case_factsService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} case_factss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Case_factsResponse)
async def update_case_facts(
    id: int,
    data: Case_factsUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing case_facts (requires ownership)"""
    logger.debug(f"Updating case_facts {id} with data: {data}")

    service = Case_factsService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Case_facts with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Case_facts not found")
        
        logger.info(f"Case_facts {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating case_facts {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating case_facts {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_case_factss_batch(
    request: Case_factsBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple case_factss by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} case_factss")
    
    service = Case_factsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} case_factss successfully")
        return {"message": f"Successfully deleted {deleted_count} case_factss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_case_facts(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single case_facts by ID (requires ownership)"""
    logger.debug(f"Deleting case_facts with id: {id}")
    
    service = Case_factsService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Case_facts with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Case_facts not found")
        
        logger.info(f"Case_facts {id} deleted successfully")
        return {"message": "Case_facts deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting case_facts {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


