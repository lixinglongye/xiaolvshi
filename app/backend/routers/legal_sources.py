from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.legal_sources import Legal_sourcesService

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/legal_sources", tags=["legal_sources"])


# ---------- Pydantic Schemas ----------
class Legal_sourcesData(BaseModel):
    """Entity data schema (for create/update)"""
    source_type: str
    title: str
    code_ref: str = None
    content_snippet: str = None
    url: str = None
    jurisdiction: str = None


class Legal_sourcesUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    source_type: Optional[str] = None
    title: Optional[str] = None
    code_ref: Optional[str] = None
    content_snippet: Optional[str] = None
    url: Optional[str] = None
    jurisdiction: Optional[str] = None


class Legal_sourcesResponse(BaseModel):
    """Entity response schema"""
    id: int
    source_type: str
    title: str
    code_ref: Optional[str] = None
    content_snippet: Optional[str] = None
    url: Optional[str] = None
    jurisdiction: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Legal_sourcesListResponse(BaseModel):
    """List response schema"""
    items: List[Legal_sourcesResponse]
    total: int
    skip: int
    limit: int


class Legal_sourcesBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Legal_sourcesData]


class Legal_sourcesBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Legal_sourcesUpdateData


class Legal_sourcesBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Legal_sourcesBatchUpdateItem]


class Legal_sourcesBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Legal_sourcesListResponse)
async def query_legal_sourcess(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Query legal_sourcess with filtering, sorting, and pagination"""
    logger.debug(f"Querying legal_sourcess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Legal_sourcesService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
        )
        logger.debug(f"Found {result['total']} legal_sourcess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying legal_sourcess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Legal_sourcesListResponse)
async def query_legal_sourcess_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query legal_sourcess with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying legal_sourcess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Legal_sourcesService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} legal_sourcess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying legal_sourcess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Legal_sourcesResponse)
async def get_legal_sources(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get a single legal_sources by ID"""
    logger.debug(f"Fetching legal_sources with id: {id}, fields={fields}")
    
    service = Legal_sourcesService(db)
    try:
        result = await service.get_by_id(id)
        if not result:
            logger.warning(f"Legal_sources with id {id} not found")
            raise HTTPException(status_code=404, detail="Legal_sources not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching legal_sources {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Legal_sourcesResponse, status_code=201)
async def create_legal_sources(
    data: Legal_sourcesData,
    db: AsyncSession = Depends(get_db),
):
    """Create a new legal_sources"""
    logger.debug(f"Creating new legal_sources with data: {data}")
    
    service = Legal_sourcesService(db)
    try:
        result = await service.create(data.model_dump())
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create legal_sources")
        
        logger.info(f"Legal_sources created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating legal_sources: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating legal_sources: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Legal_sourcesResponse], status_code=201)
async def create_legal_sourcess_batch(
    request: Legal_sourcesBatchCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create multiple legal_sourcess in a single request"""
    logger.debug(f"Batch creating {len(request.items)} legal_sourcess")
    
    service = Legal_sourcesService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump())
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} legal_sourcess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Legal_sourcesResponse])
async def update_legal_sourcess_batch(
    request: Legal_sourcesBatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update multiple legal_sourcess in a single request"""
    logger.debug(f"Batch updating {len(request.items)} legal_sourcess")
    
    service = Legal_sourcesService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict)
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} legal_sourcess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Legal_sourcesResponse)
async def update_legal_sources(
    id: int,
    data: Legal_sourcesUpdateData,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing legal_sources"""
    logger.debug(f"Updating legal_sources {id} with data: {data}")

    service = Legal_sourcesService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict)
        if not result:
            logger.warning(f"Legal_sources with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Legal_sources not found")
        
        logger.info(f"Legal_sources {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating legal_sources {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating legal_sources {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_legal_sourcess_batch(
    request: Legal_sourcesBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple legal_sourcess by their IDs"""
    logger.debug(f"Batch deleting {len(request.ids)} legal_sourcess")
    
    service = Legal_sourcesService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id)
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} legal_sourcess successfully")
        return {"message": f"Successfully deleted {deleted_count} legal_sourcess", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_legal_sources(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a single legal_sources by ID"""
    logger.debug(f"Deleting legal_sources with id: {id}")
    
    service = Legal_sourcesService(db)
    try:
        success = await service.delete(id)
        if not success:
            logger.warning(f"Legal_sources with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Legal_sources not found")
        
        logger.info(f"Legal_sources {id} deleted successfully")
        return {"message": "Legal_sources deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting legal_sources {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


