from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.deletion_requests import Deletion_requestsService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/deletion_requests", tags=["deletion_requests"])


# ---------- Pydantic Schemas ----------
class Deletion_requestsData(BaseModel):
    """Entity data schema (for create/update)"""
    document_id: int
    reason: str = None
    status: str = None


class Deletion_requestsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    document_id: Optional[int] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class Deletion_requestsResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    document_id: int
    reason: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Deletion_requestsListResponse(BaseModel):
    """List response schema"""
    items: List[Deletion_requestsResponse]
    total: int
    skip: int
    limit: int


class Deletion_requestsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Deletion_requestsData]


class Deletion_requestsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Deletion_requestsUpdateData


class Deletion_requestsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Deletion_requestsBatchUpdateItem]


class Deletion_requestsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Deletion_requestsListResponse)
async def query_deletion_requestss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query deletion_requestss with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying deletion_requestss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Deletion_requestsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} deletion_requestss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying deletion_requestss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Deletion_requestsListResponse)
async def query_deletion_requestss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query deletion_requestss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying deletion_requestss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Deletion_requestsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} deletion_requestss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying deletion_requestss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Deletion_requestsResponse)
async def get_deletion_requests(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single deletion_requests by ID (user can only see their own records)"""
    logger.debug(f"Fetching deletion_requests with id: {id}, fields={fields}")
    
    service = Deletion_requestsService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Deletion_requests with id {id} not found")
            raise HTTPException(status_code=404, detail="Deletion_requests not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching deletion_requests {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Deletion_requestsResponse, status_code=201)
async def create_deletion_requests(
    data: Deletion_requestsData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new deletion_requests"""
    logger.debug(f"Creating new deletion_requests with data: {data}")
    
    service = Deletion_requestsService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create deletion_requests")
        
        logger.info(f"Deletion_requests created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating deletion_requests: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating deletion_requests: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Deletion_requestsResponse], status_code=201)
async def create_deletion_requestss_batch(
    request: Deletion_requestsBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple deletion_requestss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} deletion_requestss")
    
    service = Deletion_requestsService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} deletion_requestss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Deletion_requestsResponse])
async def update_deletion_requestss_batch(
    request: Deletion_requestsBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple deletion_requestss in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} deletion_requestss")
    
    service = Deletion_requestsService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} deletion_requestss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Deletion_requestsResponse)
async def update_deletion_requests(
    id: int,
    data: Deletion_requestsUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing deletion_requests (requires ownership)"""
    logger.debug(f"Updating deletion_requests {id} with data: {data}")

    service = Deletion_requestsService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Deletion_requests with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Deletion_requests not found")
        
        logger.info(f"Deletion_requests {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating deletion_requests {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating deletion_requests {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_deletion_requestss_batch(
    request: Deletion_requestsBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple deletion_requestss by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} deletion_requestss")
    
    service = Deletion_requestsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} deletion_requestss successfully")
        return {"message": f"Successfully deleted {deleted_count} deletion_requestss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_deletion_requests(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single deletion_requests by ID (requires ownership)"""
    logger.debug(f"Deleting deletion_requests with id: {id}")
    
    service = Deletion_requestsService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Deletion_requests with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Deletion_requests not found")
        
        logger.info(f"Deletion_requests {id} deleted successfully")
        return {"message": "Deletion_requests deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting deletion_requests {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


