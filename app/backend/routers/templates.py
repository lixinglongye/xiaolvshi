from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.templates import TemplatesService

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/templates", tags=["templates"])


# ---------- Pydantic Schemas ----------
class TemplatesData(BaseModel):
    """Entity data schema (for create/update)"""
    doc_type: str
    title: str
    content: str = None
    is_active: bool = None
    language: str = None


class TemplatesUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    doc_type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None
    language: Optional[str] = None


class TemplatesResponse(BaseModel):
    """Entity response schema"""
    id: int
    doc_type: str
    title: str
    content: Optional[str] = None
    is_active: Optional[bool] = None
    language: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplatesListResponse(BaseModel):
    """List response schema"""
    items: List[TemplatesResponse]
    total: int
    skip: int
    limit: int


class TemplatesBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[TemplatesData]


class TemplatesBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: TemplatesUpdateData


class TemplatesBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[TemplatesBatchUpdateItem]


class TemplatesBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=TemplatesListResponse)
async def query_templatess(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Query templatess with filtering, sorting, and pagination"""
    logger.debug(f"Querying templatess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = TemplatesService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
        )
        logger.debug(f"Found {result['total']} templatess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying templatess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=TemplatesListResponse)
async def query_templatess_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query templatess with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying templatess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = TemplatesService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} templatess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying templatess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=TemplatesResponse)
async def get_templates(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get a single templates by ID"""
    logger.debug(f"Fetching templates with id: {id}, fields={fields}")
    
    service = TemplatesService(db)
    try:
        result = await service.get_by_id(id)
        if not result:
            logger.warning(f"Templates with id {id} not found")
            raise HTTPException(status_code=404, detail="Templates not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching templates {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=TemplatesResponse, status_code=201)
async def create_templates(
    data: TemplatesData,
    db: AsyncSession = Depends(get_db),
):
    """Create a new templates"""
    logger.debug(f"Creating new templates with data: {data}")
    
    service = TemplatesService(db)
    try:
        result = await service.create(data.model_dump())
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create templates")
        
        logger.info(f"Templates created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating templates: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating templates: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[TemplatesResponse], status_code=201)
async def create_templatess_batch(
    request: TemplatesBatchCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create multiple templatess in a single request"""
    logger.debug(f"Batch creating {len(request.items)} templatess")
    
    service = TemplatesService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump())
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} templatess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[TemplatesResponse])
async def update_templatess_batch(
    request: TemplatesBatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update multiple templatess in a single request"""
    logger.debug(f"Batch updating {len(request.items)} templatess")
    
    service = TemplatesService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict)
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} templatess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=TemplatesResponse)
async def update_templates(
    id: int,
    data: TemplatesUpdateData,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing templates"""
    logger.debug(f"Updating templates {id} with data: {data}")

    service = TemplatesService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict)
        if not result:
            logger.warning(f"Templates with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Templates not found")
        
        logger.info(f"Templates {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating templates {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating templates {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_templatess_batch(
    request: TemplatesBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple templatess by their IDs"""
    logger.debug(f"Batch deleting {len(request.ids)} templatess")
    
    service = TemplatesService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id)
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} templatess successfully")
        return {"message": f"Successfully deleted {deleted_count} templatess", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_templates(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a single templates by ID"""
    logger.debug(f"Deleting templates with id: {id}")
    
    service = TemplatesService(db)
    try:
        success = await service.delete(id)
        if not success:
            logger.warning(f"Templates with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Templates not found")
        
        logger.info(f"Templates {id} deleted successfully")
        return {"message": "Templates deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting templates {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


