from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.cases import CasesService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/cases", tags=["cases"])


# ---------- Pydantic Schemas ----------
class CasesData(BaseModel):
    """Entity data schema (for create/update)"""
    org_id: int = None
    client_name: str = None
    title: str
    case_type: str = None
    stage: str = None
    jurisdiction: str = None
    court_or_arbitration: str = None
    role: str = None
    opposing_party: str = None
    amount: float = None
    summary: str = None
    dispute_focus: str = None
    claims: str = None
    legal_basis: str = None
    missing_materials: str = None
    next_steps: str = None
    risk_level: str = None
    owner_name: str = None
    team_members: str = None
    key_deadline: str = None
    material_count: int = None
    evidence_completeness: str = None


class CasesUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    org_id: Optional[int] = None
    client_name: Optional[str] = None
    title: Optional[str] = None
    case_type: Optional[str] = None
    stage: Optional[str] = None
    jurisdiction: Optional[str] = None
    court_or_arbitration: Optional[str] = None
    role: Optional[str] = None
    opposing_party: Optional[str] = None
    amount: Optional[float] = None
    summary: Optional[str] = None
    dispute_focus: Optional[str] = None
    claims: Optional[str] = None
    legal_basis: Optional[str] = None
    missing_materials: Optional[str] = None
    next_steps: Optional[str] = None
    risk_level: Optional[str] = None
    owner_name: Optional[str] = None
    team_members: Optional[str] = None
    key_deadline: Optional[str] = None
    material_count: Optional[int] = None
    evidence_completeness: Optional[str] = None


class CasesResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    org_id: Optional[int] = None
    client_name: Optional[str] = None
    title: str
    case_type: Optional[str] = None
    stage: Optional[str] = None
    jurisdiction: Optional[str] = None
    court_or_arbitration: Optional[str] = None
    role: Optional[str] = None
    opposing_party: Optional[str] = None
    amount: Optional[float] = None
    summary: Optional[str] = None
    dispute_focus: Optional[str] = None
    claims: Optional[str] = None
    legal_basis: Optional[str] = None
    missing_materials: Optional[str] = None
    next_steps: Optional[str] = None
    risk_level: Optional[str] = None
    owner_name: Optional[str] = None
    team_members: Optional[str] = None
    key_deadline: Optional[str] = None
    material_count: Optional[int] = None
    evidence_completeness: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CasesListResponse(BaseModel):
    """List response schema"""
    items: List[CasesResponse]
    total: int
    skip: int
    limit: int


class CasesBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[CasesData]


class CasesBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: CasesUpdateData


class CasesBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[CasesBatchUpdateItem]


class CasesBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=CasesListResponse)
async def query_casess(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query casess with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying casess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = CasesService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} casess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying casess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=CasesListResponse)
async def query_casess_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query casess with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying casess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = CasesService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} casess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying casess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=CasesResponse)
async def get_cases(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single cases by ID (user can only see their own records)"""
    logger.debug(f"Fetching cases with id: {id}, fields={fields}")
    
    service = CasesService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Cases with id {id} not found")
            raise HTTPException(status_code=404, detail="Cases not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching cases {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=CasesResponse, status_code=201)
async def create_cases(
    data: CasesData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new cases"""
    logger.debug(f"Creating new cases with data: {data}")
    
    service = CasesService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create cases")
        
        logger.info(f"Cases created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating cases: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating cases: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[CasesResponse], status_code=201)
async def create_casess_batch(
    request: CasesBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple casess in a single request"""
    logger.debug(f"Batch creating {len(request.items)} casess")
    
    service = CasesService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} casess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[CasesResponse])
async def update_casess_batch(
    request: CasesBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple casess in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} casess")
    
    service = CasesService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} casess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=CasesResponse)
async def update_cases(
    id: int,
    data: CasesUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing cases (requires ownership)"""
    logger.debug(f"Updating cases {id} with data: {data}")

    service = CasesService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Cases with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Cases not found")
        
        logger.info(f"Cases {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating cases {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating cases {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_casess_batch(
    request: CasesBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple casess by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} casess")
    
    service = CasesService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} casess successfully")
        return {"message": f"Successfully deleted {deleted_count} casess", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_cases(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single cases by ID (requires ownership)"""
    logger.debug(f"Deleting cases with id: {id}")
    
    service = CasesService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Cases with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Cases not found")
        
        logger.info(f"Cases {id} deleted successfully")
        return {"message": "Cases deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cases {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


