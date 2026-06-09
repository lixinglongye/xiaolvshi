from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.database import get_db
from fastapi import APIRouter, Body, Depends, HTTPException, status
from services.aihub import AIHubService
from services.legal_rag_embedding_batch_preview import (
    LegalRagEmbeddingBatchPreviewService,
    LegalRagEmbeddingBatchPreviewValidationError,
)
from services.legal_rag_index_binding import (
    SAFE_SOURCE_METADATA_FIELDS,
    LegalRagIndexBindingService,
)
from services.legal_source_durable_index_plan import FORBIDDEN_FIELDS
from services.legal_source_index_repository import LegalSourceIndexValidationError
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/api/v1/legal-rag", tags=["legal_rag"])


@router.post("/retrieval-plan")
async def build_legal_rag_retrieval_plan(
    payload: dict[str, Any] | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
):
    service = LegalRagIndexBindingService()
    try:
        plan = await service.build_retrieval_plan(db, payload or {})
        return {"success": True, "data": _safe_retrieval_plan(plan)}
    except (LegalSourceIndexValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=_safe_error_detail(exc)) from exc


@router.post("/evaluate")
async def evaluate_legal_rag_retrieval(
    payload: dict[str, Any] | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
):
    service = LegalRagIndexBindingService()
    try:
        request = payload or {}
        filters = request.get("filters") or {}
        if not isinstance(filters, dict):
            raise ValueError("legal_rag_filters_must_be_object")

        plan = await service.build_retrieval_plan(db, filters)
        result = service.evaluate_retrieval(
            plan,
            retrieved_source_ids=request.get("retrieved_source_ids"),
            answer_citation_source_ids=request.get("answer_citation_source_ids"),
            verified_claim_count=request.get("verified_claim_count", 0),
            total_claim_count=request.get("total_claim_count"),
            unsupported_claims=request.get("unsupported_claims"),
            pii_findings=request.get("pii_findings"),
        )
        return {"success": True, "data": _safe_evaluation_result(result)}
    except (LegalSourceIndexValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=_safe_error_detail(exc)) from exc


@router.post("/embedding-batch-preview")
async def preview_legal_rag_embedding_batch(
    payload: dict[str, Any] | None = Body(default=None),
):
    service = LegalRagEmbeddingBatchPreviewService(aihub_service=AIHubService())
    try:
        preview = await service.build_preview(payload or {})
        return {"success": True, "data": _drop_forbidden_keys(preview)}
    except LegalRagEmbeddingBatchPreviewValidationError as exc:
        raise HTTPException(status_code=400, detail=_safe_error_detail(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "legal_rag_embedding_preview_unavailable",
                "message": "Legal RAG embedding preview requires a configured AI gateway.",
            },
        ) from exc


def _safe_retrieval_plan(plan: dict[str, Any]) -> dict[str, Any]:
    safe = _drop_forbidden_keys(plan)
    selected_sources = safe.get("selected_sources")
    if isinstance(selected_sources, list):
        safe["selected_sources"] = [
            {key: value for key, value in source.items() if key in SAFE_SOURCE_METADATA_FIELDS}
            for source in selected_sources
            if isinstance(source, dict)
        ]
    return safe


def _safe_evaluation_result(result: dict[str, Any]) -> dict[str, Any]:
    safe = _drop_forbidden_keys(result)
    retrieval_plan = safe.get("retrieval_plan")
    if isinstance(retrieval_plan, dict):
        safe["retrieval_plan"] = _safe_retrieval_plan(retrieval_plan)

    evaluation_input = safe.get("evaluation_input")
    if isinstance(evaluation_input, dict):
        unsupported_claims = evaluation_input.pop("unsupported_claims", [])
        pii_findings = evaluation_input.pop("pii_findings", [])
        evaluation_input["unsupported_claim_count"] = len(unsupported_claims) if isinstance(unsupported_claims, list) else 0
        evaluation_input["pii_finding_count"] = len(pii_findings) if isinstance(pii_findings, list) else 0

    return safe


def _drop_forbidden_keys(value: Any) -> Any:
    forbidden = {str(field).lower() for field in FORBIDDEN_FIELDS}
    if isinstance(value, dict):
        return {
            key: _drop_forbidden_keys(child)
            for key, child in value.items()
            if str(key).lower() not in forbidden
        }
    if isinstance(value, list):
        return [_drop_forbidden_keys(item) for item in value]
    if isinstance(value, tuple):
        return [_drop_forbidden_keys(item) for item in value]
    return deepcopy(value)


def _safe_error_detail(exc: Exception) -> dict[str, Any]:
    detail: dict[str, Any] = {
        "error": "invalid_legal_rag_request",
        "message": "Legal RAG request failed validation.",
    }
    validation_report = getattr(exc, "validation_report", None)
    if isinstance(validation_report, dict):
        detail["validation"] = {
            "status": validation_report.get("status"),
            "failures": _list_text(validation_report.get("failures")),
            "warnings": _list_text(validation_report.get("warnings")),
            "forbidden_fields_present": _list_text(validation_report.get("forbidden_fields_present")),
            "sensitive_value_findings": [
                {"path": str(item.get("path") or ""), "type": str(item.get("type") or "")}
                for item in validation_report.get("sensitive_value_findings", [])
                if isinstance(item, dict)
            ],
        }
    return detail


def _list_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [text for text in (str(item or "").strip() for item in value) if text]
    text = str(value or "").strip()
    return [text] if text else []
