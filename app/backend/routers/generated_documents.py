from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.generated_documents import Generated_documentsService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/generated_documents", tags=["generated_documents"])


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
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new generated_documents"""
    logger.debug(f"Creating new generated_documents with data: {data}")
    
    service = Generated_documentsService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create generated_documents")
        
        logger.info(f"Generated_documents created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating generated_documents: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating generated_documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Generated_documentsResponse], status_code=201)
async def create_generated_documentss_batch(
    request: Generated_documentsBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple generated_documentss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} generated_documentss")
    
    service = Generated_documentsService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} generated_documentss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


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
    logger.debug(f"Updating generated_documents {id} with data: {data}")

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


