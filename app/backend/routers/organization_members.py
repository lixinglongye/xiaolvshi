from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.organization_members import Organization_membersService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/organization_members", tags=["organization_members"])


# ---------- Pydantic Schemas ----------
class Organization_membersData(BaseModel):
    """Entity data schema (for create/update)"""
    org_id: int
    member_email: str
    member_user_id: str = None
    role: str = None
    status: str = None


class Organization_membersUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    org_id: Optional[int] = None
    member_email: Optional[str] = None
    member_user_id: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class Organization_membersResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    org_id: int
    member_email: str
    member_user_id: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Organization_membersListResponse(BaseModel):
    """List response schema"""
    items: List[Organization_membersResponse]
    total: int
    skip: int
    limit: int


class Organization_membersBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Organization_membersData]


class Organization_membersBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Organization_membersUpdateData


class Organization_membersBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Organization_membersBatchUpdateItem]


class Organization_membersBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Organization_membersListResponse)
async def query_organization_memberss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query organization_memberss with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying organization_memberss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Organization_membersService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} organization_memberss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying organization_memberss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Organization_membersListResponse)
async def query_organization_memberss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query organization_memberss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying organization_memberss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Organization_membersService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} organization_memberss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying organization_memberss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Organization_membersResponse)
async def get_organization_members(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single organization_members by ID (user can only see their own records)"""
    logger.debug(f"Fetching organization_members with id: {id}, fields={fields}")
    
    service = Organization_membersService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Organization_members with id {id} not found")
            raise HTTPException(status_code=404, detail="Organization_members not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching organization_members {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Organization_membersResponse, status_code=201)
async def create_organization_members(
    data: Organization_membersData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new organization_members"""
    logger.debug(f"Creating new organization_members with data: {data}")
    
    service = Organization_membersService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create organization_members")
        
        logger.info(f"Organization_members created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating organization_members: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating organization_members: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Organization_membersResponse], status_code=201)
async def create_organization_memberss_batch(
    request: Organization_membersBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple organization_memberss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} organization_memberss")
    
    service = Organization_membersService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} organization_memberss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Organization_membersResponse])
async def update_organization_memberss_batch(
    request: Organization_membersBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple organization_memberss in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} organization_memberss")
    
    service = Organization_membersService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} organization_memberss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Organization_membersResponse)
async def update_organization_members(
    id: int,
    data: Organization_membersUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing organization_members (requires ownership)"""
    logger.debug(f"Updating organization_members {id} with data: {data}")

    service = Organization_membersService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Organization_members with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Organization_members not found")
        
        logger.info(f"Organization_members {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating organization_members {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating organization_members {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_organization_memberss_batch(
    request: Organization_membersBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple organization_memberss by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} organization_memberss")
    
    service = Organization_membersService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} organization_memberss successfully")
        return {"message": f"Successfully deleted {deleted_count} organization_memberss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_organization_members(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single organization_members by ID (requires ownership)"""
    logger.debug(f"Deleting organization_members with id: {id}")
    
    service = Organization_membersService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Organization_members with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Organization_members not found")
        
        logger.info(f"Organization_members {id} deleted successfully")
        return {"message": "Organization_members deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting organization_members {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


