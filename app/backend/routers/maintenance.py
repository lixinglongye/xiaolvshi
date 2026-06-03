from typing import Literal

from fastapi import APIRouter, Query
from services.feedback_roadmap_alignment import FeedbackRoadmapAlignmentService
from services.legal_fixture_improvement import LegalFixtureImprovementService
from services.legal_review_benchmark import LegalReviewBenchmarkService
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


@router.get("/feedback-roadmap")
async def get_feedback_roadmap_mapping():
    """Return feedback-to-roadmap mapping rules for maintenance planning."""
    return {
        "success": True,
        "data": FeedbackRoadmapAlignmentService().build_mapping_catalog(),
    }


@router.get("/legal-review-benchmark")
async def get_legal_review_benchmark_suite():
    """Return the deterministic benchmark suite for legal-review pipeline changes."""
    service = LegalReviewBenchmarkService()
    return {
        "success": True,
        "data": service.evaluate(),
    }


@router.post("/legal-review-benchmark")
async def evaluate_legal_review_benchmark(run_results: dict[str, dict]):
    """Evaluate supplied benchmark results for release planning."""
    service = LegalReviewBenchmarkService()
    return {
        "success": True,
        "data": service.evaluate(run_results),
    }


@router.get("/legal-review-benchmark/fixture-smoke")
async def get_legal_review_fixture_smoke_template():
    """Return local synthetic legal document fixture smoke-test templates."""
    service = LegalReviewBenchmarkService()
    return {
        "success": True,
        "data": service.evaluate_fixture_smoke(),
    }


@router.post("/legal-review-benchmark/fixture-smoke")
async def evaluate_legal_review_fixture_smoke(observations: dict[str, dict]):
    """Evaluate supplied legal fixture smoke-test observations."""
    service = LegalReviewBenchmarkService()
    return {
        "success": True,
        "data": service.evaluate_fixture_smoke(observations),
    }


@router.get("/legal-review-benchmark/fixture-improvements")
async def get_legal_review_fixture_improvement_template():
    """Return an empty legal fixture improvement plan template."""
    return {
        "success": True,
        "data": LegalFixtureImprovementService().build_plan(),
    }


@router.post("/legal-review-benchmark/fixture-improvements")
async def build_legal_review_fixture_improvement_plan(observations: dict[str, dict]):
    """Convert fixture smoke observations into prompt and report-schema improvement actions."""
    return {
        "success": True,
        "data": LegalFixtureImprovementService().build_plan(observations),
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
