from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.case_tasks import Case_tasksService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/case_tasks", tags=["case_tasks"])


# ---------- Pydantic Schemas ----------
class Case_tasksData(BaseModel):
    """Entity data schema (for create/update)"""
    case_id: int
    title: str
    description: str = None
    assigned_to: str = None
    due_date: str = None
    priority: str = None
    status: str = None
    related_object_type: str = None
    related_object_id: int = None


class Case_tasksUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    case_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    related_object_type: Optional[str] = None
    related_object_id: Optional[int] = None


class Case_tasksResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    case_id: int
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    related_object_type: Optional[str] = None
    related_object_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Case_tasksListResponse(BaseModel):
    """List response schema"""
    items: List[Case_tasksResponse]
    total: int
    skip: int
    limit: int


class Case_tasksBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Case_tasksData]


class Case_tasksBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Case_tasksUpdateData


class Case_tasksBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Case_tasksBatchUpdateItem]


class Case_tasksBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Case_tasksListResponse)
async def query_case_taskss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query case_taskss with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying case_taskss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Case_tasksService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} case_taskss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying case_taskss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Case_tasksListResponse)
async def query_case_taskss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query case_taskss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying case_taskss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Case_tasksService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} case_taskss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying case_taskss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Case_tasksResponse)
async def get_case_tasks(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single case_tasks by ID (user can only see their own records)"""
    logger.debug(f"Fetching case_tasks with id: {id}, fields={fields}")
    
    service = Case_tasksService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Case_tasks with id {id} not found")
            raise HTTPException(status_code=404, detail="Case_tasks not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching case_tasks {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Case_tasksResponse, status_code=201)
async def create_case_tasks(
    data: Case_tasksData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new case_tasks"""
    logger.debug(f"Creating new case_tasks with data: {data}")
    
    service = Case_tasksService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create case_tasks")
        
        logger.info(f"Case_tasks created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating case_tasks: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating case_tasks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Case_tasksResponse], status_code=201)
async def create_case_taskss_batch(
    request: Case_tasksBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple case_taskss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} case_taskss")
    
    service = Case_tasksService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} case_taskss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Case_tasksResponse])
async def update_case_taskss_batch(
    request: Case_tasksBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple case_taskss in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} case_taskss")
    
    service = Case_tasksService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} case_taskss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Case_tasksResponse)
async def update_case_tasks(
    id: int,
    data: Case_tasksUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing case_tasks (requires ownership)"""
    logger.debug(f"Updating case_tasks {id} with data: {data}")

    service = Case_tasksService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Case_tasks with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Case_tasks not found")
        
        logger.info(f"Case_tasks {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating case_tasks {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating case_tasks {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_case_taskss_batch(
    request: Case_tasksBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple case_taskss by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} case_taskss")
    
    service = Case_tasksService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} case_taskss successfully")
        return {"message": f"Successfully deleted {deleted_count} case_taskss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_case_tasks(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single case_tasks by ID (requires ownership)"""
    logger.debug(f"Deleting case_tasks with id: {id}")
    
    service = Case_tasksService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Case_tasks with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Case_tasks not found")
        
        logger.info(f"Case_tasks {id} deleted successfully")
        return {"message": "Case_tasks deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting case_tasks {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


