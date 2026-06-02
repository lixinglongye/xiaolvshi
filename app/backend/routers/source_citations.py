from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.source_citations import Source_citationsService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/source_citations", tags=["source_citations"])


# ---------- Pydantic Schemas ----------
class Source_citationsData(BaseModel):
    """Entity data schema (for create/update)"""
    risk_item_id: int
    legal_source_id: int
    snippet: str = None


class Source_citationsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    risk_item_id: Optional[int] = None
    legal_source_id: Optional[int] = None
    snippet: Optional[str] = None


class Source_citationsResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    risk_item_id: int
    legal_source_id: int
    snippet: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Source_citationsListResponse(BaseModel):
    """List response schema"""
    items: List[Source_citationsResponse]
    total: int
    skip: int
    limit: int


class Source_citationsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Source_citationsData]


class Source_citationsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Source_citationsUpdateData


class Source_citationsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Source_citationsBatchUpdateItem]


class Source_citationsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Source_citationsListResponse)
async def query_source_citationss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query source_citationss with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying source_citationss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Source_citationsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} source_citationss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying source_citationss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Source_citationsListResponse)
async def query_source_citationss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query source_citationss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying source_citationss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Source_citationsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} source_citationss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying source_citationss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Source_citationsResponse)
async def get_source_citations(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single source_citations by ID (user can only see their own records)"""
    logger.debug(f"Fetching source_citations with id: {id}, fields={fields}")
    
    service = Source_citationsService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Source_citations with id {id} not found")
            raise HTTPException(status_code=404, detail="Source_citations not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching source_citations {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Source_citationsResponse, status_code=201)
async def create_source_citations(
    data: Source_citationsData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new source_citations"""
    logger.debug(f"Creating new source_citations with data: {data}")
    
    service = Source_citationsService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create source_citations")
        
        logger.info(f"Source_citations created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating source_citations: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating source_citations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Source_citationsResponse], status_code=201)
async def create_source_citationss_batch(
    request: Source_citationsBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple source_citationss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} source_citationss")
    
    service = Source_citationsService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} source_citationss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Source_citationsResponse])
async def update_source_citationss_batch(
    request: Source_citationsBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple source_citationss in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} source_citationss")
    
    service = Source_citationsService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} source_citationss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Source_citationsResponse)
async def update_source_citations(
    id: int,
    data: Source_citationsUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing source_citations (requires ownership)"""
    logger.debug(f"Updating source_citations {id} with data: {data}")

    service = Source_citationsService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Source_citations with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Source_citations not found")
        
        logger.info(f"Source_citations {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating source_citations {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating source_citations {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_source_citationss_batch(
    request: Source_citationsBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple source_citationss by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} source_citationss")
    
    service = Source_citationsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} source_citationss successfully")
        return {"message": f"Successfully deleted {deleted_count} source_citationss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_source_citations(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single source_citations by ID (requires ownership)"""
    logger.debug(f"Deleting source_citations with id: {id}")
    
    service = Source_citationsService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Source_citations with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Source_citations not found")
        
        logger.info(f"Source_citations {id} deleted successfully")
        return {"message": "Source_citations deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting source_citations {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


