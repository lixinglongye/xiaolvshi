from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.review_reports import Review_reportsService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/review_reports", tags=["review_reports"])


# ---------- Pydantic Schemas ----------
class Review_reportsData(BaseModel):
    """Entity data schema (for create/update)"""
    document_id: int
    contract_type: str = None
    user_role: str = None
    risk_score: int = None
    risk_level: str = None
    signing_recommendation: str = None
    executive_summary: str = None
    contract_basic_info: str = None
    risk_matrix: str = None
    missing_clause_checklist: str = None
    favorable_clauses: str = None
    legal_source_appendix: str = None
    full_report_json: str = None
    pipeline_trace_json: str = None
    disclaimer: str = None
    status: str = None
    is_paid: bool = None


class Review_reportsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    document_id: Optional[int] = None
    contract_type: Optional[str] = None
    user_role: Optional[str] = None
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    signing_recommendation: Optional[str] = None
    executive_summary: Optional[str] = None
    contract_basic_info: Optional[str] = None
    risk_matrix: Optional[str] = None
    missing_clause_checklist: Optional[str] = None
    favorable_clauses: Optional[str] = None
    legal_source_appendix: Optional[str] = None
    full_report_json: Optional[str] = None
    pipeline_trace_json: Optional[str] = None
    disclaimer: Optional[str] = None
    status: Optional[str] = None
    is_paid: Optional[bool] = None


class Review_reportsResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    document_id: int
    contract_type: Optional[str] = None
    user_role: Optional[str] = None
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    signing_recommendation: Optional[str] = None
    executive_summary: Optional[str] = None
    contract_basic_info: Optional[str] = None
    risk_matrix: Optional[str] = None
    missing_clause_checklist: Optional[str] = None
    favorable_clauses: Optional[str] = None
    legal_source_appendix: Optional[str] = None
    full_report_json: Optional[str] = None
    pipeline_trace_json: Optional[str] = None
    disclaimer: Optional[str] = None
    status: Optional[str] = None
    is_paid: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Review_reportsListResponse(BaseModel):
    """List response schema"""
    items: List[Review_reportsResponse]
    total: int
    skip: int
    limit: int


class Review_reportsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Review_reportsData]


class Review_reportsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Review_reportsUpdateData


class Review_reportsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Review_reportsBatchUpdateItem]


class Review_reportsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Review_reportsListResponse)
async def query_review_reportss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query review_reportss with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying review_reportss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Review_reportsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} review_reportss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying review_reportss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Review_reportsListResponse)
async def query_review_reportss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query review_reportss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying review_reportss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Review_reportsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} review_reportss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying review_reportss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Review_reportsResponse)
async def get_review_reports(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single review_reports by ID (user can only see their own records)"""
    logger.debug(f"Fetching review_reports with id: {id}, fields={fields}")
    
    service = Review_reportsService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Review_reports with id {id} not found")
            raise HTTPException(status_code=404, detail="Review_reports not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching review_reports {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Review_reportsResponse, status_code=201)
async def create_review_reports(
    data: Review_reportsData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new review_reports"""
    logger.debug(f"Creating new review_reports with data: {data}")
    
    service = Review_reportsService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create review_reports")
        
        logger.info(f"Review_reports created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating review_reports: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating review_reports: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Review_reportsResponse], status_code=201)
async def create_review_reportss_batch(
    request: Review_reportsBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple review_reportss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} review_reportss")
    
    service = Review_reportsService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} review_reportss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Review_reportsResponse])
async def update_review_reportss_batch(
    request: Review_reportsBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple review_reportss in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} review_reportss")
    
    service = Review_reportsService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} review_reportss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Review_reportsResponse)
async def update_review_reports(
    id: int,
    data: Review_reportsUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing review_reports (requires ownership)"""
    logger.debug(f"Updating review_reports {id} with data: {data}")

    service = Review_reportsService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Review_reports with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Review_reports not found")
        
        logger.info(f"Review_reports {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating review_reports {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating review_reports {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_review_reportss_batch(
    request: Review_reportsBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple review_reportss by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} review_reportss")
    
    service = Review_reportsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} review_reportss successfully")
        return {"message": f"Successfully deleted {deleted_count} review_reportss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_review_reports(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single review_reports by ID (requires ownership)"""
    logger.debug(f"Deleting review_reports with id: {id}")
    
    service = Review_reportsService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Review_reports with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Review_reports not found")
        
        logger.info(f"Review_reports {id} deleted successfully")
        return {"message": "Review_reports deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting review_reports {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


