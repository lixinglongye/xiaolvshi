from typing import Literal

from fastapi import APIRouter, Query
from services.maintenance_evidence import MaintenanceEvidenceService
from services.release_readiness import ReleaseReadinessService
from services.user_needs_radar import UserNeedsRadarService


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


@router.get("/user-needs")
async def get_user_needs_radar():
    """Return deterministic user-need priorities for roadmap and release planning."""
    return {
        "success": True,
        "data": UserNeedsRadarService().build_radar(),
    }


@router.get("/release-readiness")
async def get_release_readiness():
    """Return the default release checklist before validation results are supplied."""
    service = ReleaseReadinessService()
    return {
        "success": True,
        "data": service.evaluate(),
        "validation_commands": service.default_validation_commands(),
    }


@router.post("/release-readiness")
async def evaluate_release_readiness(validation_results: dict[str, str]):
    """Evaluate release readiness from explicit check results."""
    service = ReleaseReadinessService()
    return {
        "success": True,
        "data": service.evaluate(validation_results),
        "validation_commands": service.default_validation_commands(),
    }
