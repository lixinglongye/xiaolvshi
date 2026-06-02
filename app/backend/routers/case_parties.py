from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.case_parties import Case_partiesService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/case_parties", tags=["case_parties"])


# ---------- Pydantic Schemas ----------
class Case_partiesData(BaseModel):
    """Entity data schema (for create/update)"""
    case_id: int
    name: str
    party_type: str = None
    identity_type: str = None
    id_number: str = None
    address: str = None
    contact: str = None
    lawyer: str = None


class Case_partiesUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    case_id: Optional[int] = None
    name: Optional[str] = None
    party_type: Optional[str] = None
    identity_type: Optional[str] = None
    id_number: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    lawyer: Optional[str] = None


class Case_partiesResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    case_id: int
    name: str
    party_type: Optional[str] = None
    identity_type: Optional[str] = None
    id_number: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    lawyer: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Case_partiesListResponse(BaseModel):
    """List response schema"""
    items: List[Case_partiesResponse]
    total: int
    skip: int
    limit: int


class Case_partiesBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Case_partiesData]


class Case_partiesBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Case_partiesUpdateData


class Case_partiesBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Case_partiesBatchUpdateItem]


class Case_partiesBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Case_partiesListResponse)
async def query_case_partiess(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query case_partiess with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying case_partiess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Case_partiesService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} case_partiess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying case_partiess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Case_partiesListResponse)
async def query_case_partiess_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query case_partiess with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying case_partiess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Case_partiesService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} case_partiess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying case_partiess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Case_partiesResponse)
async def get_case_parties(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single case_parties by ID (user can only see their own records)"""
    logger.debug(f"Fetching case_parties with id: {id}, fields={fields}")
    
    service = Case_partiesService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Case_parties with id {id} not found")
            raise HTTPException(status_code=404, detail="Case_parties not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching case_parties {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Case_partiesResponse, status_code=201)
async def create_case_parties(
    data: Case_partiesData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new case_parties"""
    logger.debug(f"Creating new case_parties with data: {data}")
    
    service = Case_partiesService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create case_parties")
        
        logger.info(f"Case_parties created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating case_parties: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating case_parties: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Case_partiesResponse], status_code=201)
async def create_case_partiess_batch(
    request: Case_partiesBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple case_partiess in a single request"""
    logger.debug(f"Batch creating {len(request.items)} case_partiess")
    
    service = Case_partiesService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} case_partiess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Case_partiesResponse])
async def update_case_partiess_batch(
    request: Case_partiesBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple case_partiess in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} case_partiess")
    
    service = Case_partiesService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} case_partiess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Case_partiesResponse)
async def update_case_parties(
    id: int,
    data: Case_partiesUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing case_parties (requires ownership)"""
    logger.debug(f"Updating case_parties {id} with data: {data}")

    service = Case_partiesService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Case_parties with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Case_parties not found")
        
        logger.info(f"Case_parties {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating case_parties {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating case_parties {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_case_partiess_batch(
    request: Case_partiesBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple case_partiess by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} case_partiess")
    
    service = Case_partiesService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} case_partiess successfully")
        return {"message": f"Successfully deleted {deleted_count} case_partiess", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_case_parties(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single case_parties by ID (requires ownership)"""
    logger.debug(f"Deleting case_parties with id: {id}")
    
    service = Case_partiesService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Case_parties with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Case_parties not found")
        
        logger.info(f"Case_parties {id} deleted successfully")
        return {"message": "Case_parties deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting case_parties {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


