from routers.crud_helpers import parse_query_param, partial_update_data
import logging
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.feedback_tickets import Feedback_ticketsService
from services.feedback_roadmap_alignment import FeedbackRoadmapAlignmentService
from services.feedback_triage import FeedbackTriageService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/feedback_tickets", tags=["feedback_tickets"])


# ---------- Pydantic Schemas ----------
class Feedback_ticketsData(BaseModel):
    """Entity data schema (for create/update)"""
    category: str
    content: str
    status: str = None
    contact: str = None
    priority: str = None
    assignee: str = None
    resolution_note: str = None


class Feedback_ticketsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    category: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    contact: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    resolution_note: Optional[str] = None


class Feedback_ticketsResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    category: str
    content: str
    status: Optional[str] = None
    contact: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    resolution_note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Feedback_ticketsListResponse(BaseModel):
    """List response schema"""
    items: List[Feedback_ticketsResponse]
    total: int
    skip: int
    limit: int


class Feedback_ticketsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Feedback_ticketsData]


class Feedback_ticketsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Feedback_ticketsUpdateData


class Feedback_ticketsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Feedback_ticketsBatchUpdateItem]


class Feedback_ticketsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


class FeedbackTriagePreviewRequest(BaseModel):
    category: str
    content: str


class FeedbackTriagePreviewResponse(BaseModel):
    status: str
    priority: str
    assignee: str
    sla_hours: int
    labels: List[str]
    matched_rule_ids: List[str]
    reasons: List[str]
    operator_actions: List[str]
    summary: str
    roadmap_alignment: Optional[dict] = None


# ---------- Routes ----------
@router.get("", response_model=Feedback_ticketsListResponse)
async def query_feedback_ticketss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query feedback_ticketss with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying feedback_ticketss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Feedback_ticketsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} feedback_ticketss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying feedback_ticketss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Feedback_ticketsListResponse)
async def query_feedback_ticketss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query feedback_ticketss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying feedback_ticketss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Feedback_ticketsService(db)
    try:
        query_dict = parse_query_param(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} feedback_ticketss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying feedback_ticketss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/triage-preview", response_model=FeedbackTriagePreviewResponse)
async def preview_feedback_triage(
    data: FeedbackTriagePreviewRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Preview deterministic feedback triage without creating a ticket."""
    _ = current_user
    triage = FeedbackTriageService().triage(data.model_dump())
    triage["roadmap_alignment"] = FeedbackRoadmapAlignmentService().align(data.model_dump())
    return triage


@router.get("/{id}", response_model=Feedback_ticketsResponse)
async def get_feedback_tickets(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single feedback_tickets by ID (user can only see their own records)"""
    logger.debug(f"Fetching feedback_tickets with id: {id}, fields={fields}")
    
    service = Feedback_ticketsService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Feedback_tickets with id {id} not found")
            raise HTTPException(status_code=404, detail="Feedback_tickets not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching feedback_tickets {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Feedback_ticketsResponse, status_code=201)
async def create_feedback_tickets(
    data: Feedback_ticketsData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new feedback_tickets"""
    logger.debug(f"Creating new feedback_tickets with data: {data}")
    
    service = Feedback_ticketsService(db)
    try:
        payload = FeedbackTriageService().apply_to_payload(data.model_dump())
        result = await service.create(payload, user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create feedback_tickets")
        
        logger.info(f"Feedback_tickets created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating feedback_tickets: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating feedback_tickets: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Feedback_ticketsResponse], status_code=201)
async def create_feedback_ticketss_batch(
    request: Feedback_ticketsBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple feedback_ticketss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} feedback_ticketss")
    
    service = Feedback_ticketsService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} feedback_ticketss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Feedback_ticketsResponse])
async def update_feedback_ticketss_batch(
    request: Feedback_ticketsBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple feedback_ticketss in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} feedback_ticketss")
    
    service = Feedback_ticketsService(db)
    results = []
    
    try:
        for item in request.items:
            update_dict = partial_update_data(item.updates)
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} feedback_ticketss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Feedback_ticketsResponse)
async def update_feedback_tickets(
    id: int,
    data: Feedback_ticketsUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing feedback_tickets (requires ownership)"""
    logger.debug(f"Updating feedback_tickets {id} with data: {data}")

    service = Feedback_ticketsService(db)
    try:
        update_dict = partial_update_data(data)
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Feedback_tickets with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Feedback_tickets not found")
        
        logger.info(f"Feedback_tickets {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating feedback_tickets {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating feedback_tickets {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_feedback_ticketss_batch(
    request: Feedback_ticketsBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple feedback_ticketss by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} feedback_ticketss")
    
    service = Feedback_ticketsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} feedback_ticketss successfully")
        return {"message": f"Successfully deleted {deleted_count} feedback_ticketss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_feedback_tickets(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single feedback_tickets by ID (requires ownership)"""
    logger.debug(f"Deleting feedback_tickets with id: {id}")
    
    service = Feedback_ticketsService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Feedback_tickets with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Feedback_tickets not found")
        
        logger.info(f"Feedback_tickets {id} deleted successfully")
        return {"message": "Feedback_tickets deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feedback_tickets {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


