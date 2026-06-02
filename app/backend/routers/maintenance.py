from typing import Literal

from fastapi import APIRouter, Query
from services.maintenance_evidence import MaintenanceEvidenceService


router = APIRouter(prefix="/api/v1/maintenance", tags=["maintenance"])


@router.get("/oss-evidence")
async def get_oss_maintenance_evidence(
    language: Literal["en", "zh"] = Query(default="en", description="Form answer language."),
):
    """Return reviewable OSS maintenance evidence for support applications."""
    return {
        "success": True,
        "data": MaintenanceEvidenceService().build_profile(language),
    }
