from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.case_access_control import CaseAccessControlService
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


class CasePermissionSummaryResponse(BaseModel):
    policy_id: str
    case_id: Optional[int] = None
    actor_role: str
    role_source: str
    allowed_operations: List[str]
    approval_required_operations: List[str]
    denied_operations: List[str]
    decisions: dict
    privacy_safe: bool
    does_not_include: List[str]


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


async def _get_case_or_404(service: CasesService, case_id: int):
    case = await service.get_by_id(case_id)
    if not case:
        logger.warning("Cases with id %s not found", case_id)
        raise HTTPException(status_code=404, detail="Cases not found")
    return case


def _case_access_http_error(decision: dict) -> HTTPException:
    detail = {
        "policy_id": decision.get("policy_id"),
        "status": decision.get("status"),
        "actor_role": decision.get("actor_role"),
        "operation": decision.get("operation"),
        "reason": decision.get("reason") or "permission_denied",
        "approval_gate": decision.get("approval_gate"),
        "privacy_safe": True,
    }
    return HTTPException(status_code=403, detail=detail)


def _require_case_permission(case, current_user: UserResponse, operation: str) -> dict:
    decision = CaseAccessControlService().evaluate(case, current_user, operation)
    if not decision["allowed"]:
        raise _case_access_http_error(decision)
    return decision


async def _list_accessible_cases(
    service: CasesService,
    *,
    query_dict: dict,
    sort: Optional[str],
    skip: int,
    limit: int,
    current_user: UserResponse,
) -> dict:
    raw = await service.get_list(
        skip=0,
        limit=2000,
        query_dict=query_dict,
        sort=sort,
    )
    access = CaseAccessControlService()
    items = [item for item in raw["items"] if access.can_access(item, current_user, "read")]
    return {
        "items": items[skip : skip + limit],
        "total": len(items),
        "skip": skip,
        "limit": limit,
    }


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

        result = await _list_accessible_cases(
            service,
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            current_user=current_user,
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
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Query casess with runtime access filtering; this route no longer bypasses case permissions.
    logger.debug(f"Querying casess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = CasesService(db)
    try:
        query_dict = parse_query_param(query)

        result = await _list_accessible_cases(
            service,
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            current_user=current_user,
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
        result = await _get_case_or_404(service, id)
        _require_case_permission(result, current_user, "read")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching cases {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}/permissions", response_model=CasePermissionSummaryResponse)
async def get_case_permissions(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return privacy-safe runtime permissions for the current user on a case."""
    service = CasesService(db)
    try:
        case = await _get_case_or_404(service, id)
        summary = CaseAccessControlService().build_permissions_summary(case, current_user)
        if not summary["decisions"]["read"]["allowed"]:
            raise _case_access_http_error(summary["decisions"]["read"])
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching case permissions %s: %s", id, str(e), exc_info=True)
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
            case = await _get_case_or_404(service, item.id)
            _require_case_permission(case, current_user, "write")
            result = await service.update(item.id, update_dict)
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
        case = await _get_case_or_404(service, id)
        _require_case_permission(case, current_user, "write")
        result = await service.update(id, update_dict)
        
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
            case = await _get_case_or_404(service, item_id)
            _require_case_permission(case, current_user, "write")
            success = await service.delete(item_id)
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
        case = await _get_case_or_404(service, id)
        _require_case_permission(case, current_user, "write")
        success = await service.delete(id)
        
        logger.info(f"Cases {id} deleted successfully")
        return {"message": "Cases deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cases {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


