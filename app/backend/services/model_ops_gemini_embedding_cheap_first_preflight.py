from __future__ import annotations

from typing import Any

from services.model_budget import model_budget_decision
from services.model_catalog import canonical_model_id, model_profile, task_default_model


OFFICIAL_SOURCE_ROWS: tuple[dict[str, str], ...] = (
    {
        "id": "gemini-embeddings",
        "title": "Gemini embeddings",
        "url": "https://ai.google.dev/gemini-api/docs/embeddings",
        "tracked_signal": "Embedding model names, text embedding defaults, multimodal embedding scope, dimensions, and task types.",
    },
    {
        "id": "gemini-pricing",
        "title": "Gemini API pricing",
        "url": "https://ai.google.dev/pricing",
        "tracked_signal": "Embedding standard and batch prices used to keep legal RAG indexing cheap-first.",
    },
)

EMBEDDING_MODEL_TARGETS: tuple[dict[str, Any], ...] = (
    {
        "model_id": "gemini-embedding-001",
        "route_role": "cheap_first_text_embedding_default",
        "input_scope": "text",
        "batch_input_usd_per_million_tokens": 0.075,
        "default_allowed_without_review": True,
        "recommended_policy": "Use for text-only legal source chunks, title matching, source deduping, and cheap batch indexing.",
    },
    {
        "model_id": "gemini-embedding-2",
        "route_role": "multimodal_embedding_review_candidate",
        "input_scope": "text_image_audio_video_pdf",
        "batch_input_usd_per_million_tokens": 0.10,
        "default_allowed_without_review": False,
        "recommended_policy": "Use only after explicit multimodal evidence-index review; modality billing and privacy rules must be attached.",
    },
)

EMBEDDING_ROUTE_TARGETS: tuple[dict[str, Any], ...] = (
    {
        "id": "legal-rag-text-index",
        "task": "embedding",
        "display_name": "Legal RAG text index",
        "default_model": None,
        "expected_inputs": ("text", "normalized-source-metadata"),
        "route_mode": "cheap_first_text_embedding",
        "release_policy": "ready_for_text_index_preflight",
    },
    {
        "id": "source-deduping-batch-index",
        "task": "embedding",
        "display_name": "Source deduping batch index",
        "default_model": None,
        "expected_inputs": ("text", "source-title", "citation-metadata"),
        "route_mode": "cheap_first_batch_embedding",
        "release_policy": "ready_for_text_batch_preflight",
    },
    {
        "id": "multimodal-evidence-index",
        "task": "embedding",
        "display_name": "Multimodal evidence index",
        "default_model": "gemini-embedding-2",
        "expected_inputs": ("image", "audio", "video", "pdf"),
        "route_mode": "explicit_multimodal_embedding_review",
        "release_policy": "review_required_before_default_or_route_claim",
    },
)


class ModelOpsGeminiEmbeddingCheapFirstPreflightService:
    """Build metadata-only cheap-first preflight evidence for Gemini embeddings."""

    def build_preflight(self, _payload: Any = None) -> dict[str, Any]:
        embedding_rows = [self._embedding_row(target) for target in EMBEDDING_MODEL_TARGETS]
        route_rows = [self._route_row(target) for target in EMBEDDING_ROUTE_TARGETS]
        checks = self._checks(embedding_rows, route_rows)
        blocking = [check["id"] for check in checks if check["status"] == "fail"]
        warnings = [check["id"] for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking else ("review_required" if warnings else "pass")

        return {
            "id": "modelops-gemini-embedding-cheap-first-preflight",
            "title": "ModelOps Gemini embedding cheap-first preflight",
            "status": status,
            "method": {
                "type": "metadata-only-gemini-embedding-cheap-first-preflight",
                "notes": [
                    "Reviews Gemini text and multimodal embedding catalog rows against the local embedding default and budget task.",
                    "Keeps text-only embedding cheap-first while requiring explicit review before multimodal embedding route/default claims.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, indexes, databases, or the network.",
                ],
                "source_urls": [row["url"] for row in OFFICIAL_SOURCE_ROWS],
            },
            "summary": {
                "official_source_count": len(OFFICIAL_SOURCE_ROWS),
                "embedding_model_count": len(embedding_rows),
                "route_row_count": len(route_rows),
                "cheap_first_default_model": task_default_model("embedding"),
                "cheap_first_default_canonical_model": canonical_model_id(task_default_model("embedding")),
                "text_embedding_ready_count": sum(
                    1 for row in embedding_rows if row["route_role"] == "cheap_first_text_embedding_default"
                ),
                "multimodal_review_count": sum(
                    1 for row in embedding_rows if row["route_role"] == "multimodal_embedding_review_candidate"
                ),
                "over_budget_candidate_count": sum(1 for row in embedding_rows if row["is_over_budget"]),
                "default_allowed_model_count": sum(1 for row in embedding_rows if row["default_allowed_without_review"]),
                "review_route_count": sum(1 for row in route_rows if row["route_status"] == "review_required"),
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "model_called": False,
                "index_written": False,
                "default_changed": False,
                "raw_payload_echoed": False,
            },
            "official_source_rows": [dict(row) for row in OFFICIAL_SOURCE_ROWS],
            "embedding_rows": embedding_rows,
            "route_rows": route_rows,
            "checks": checks,
            "blocking_check_ids": blocking,
            "warning_check_ids": warnings,
            "recommended_actions": self._recommended_actions(embedding_rows, route_rows),
            "privacy_boundary": {
                "metadata_only": True,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "index_written": False,
                "configuration_written": False,
                "default_changed": False,
                "credentials_included": False,
                "headers_included": False,
                "prompts_included": False,
                "request_bodies_included": False,
                "response_bodies_included": False,
                "raw_payload_echoed": False,
                "raw_embedding_vectors_included": False,
                "raw_legal_text_included": False,
                "source_chunks_included": False,
                "emails_included": False,
                "output_scope": "model ids, task labels, prices, budget modes, route labels, checks, and validation commands only",
            },
            "claim_boundary": {
                "live_embedding_route_claimed": False,
                "embedding_index_created": False,
                "multimodal_embedding_default_claimed": False,
                "automatic_default_change_claimed": False,
                "pricing_accuracy_claimed": False,
                "gateway_execution_claimed": False,
                "allowed_claim": "The repository exposes cataloged cheap-first Gemini embedding defaults and metadata-only preflight evidence.",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_gemini_embedding_cheap_first_preflight.py tests/test_model_catalog.py tests/test_model_budget.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_modelops_gemini_cheap_first_coverage_gate.py tests/test_model_ops_gemini_cheap_first_route_preflight.py tests/test_model_configuration_audit.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _embedding_row(self, target: dict[str, Any]) -> dict[str, Any]:
        model_id = str(target["model_id"])
        profile = model_profile(model_id)
        budget = model_budget_decision(model_id, task="embedding")
        pricing_status = "priced" if profile and profile.input_usd_per_million_tokens is not None else "missing"
        return {
            "model_id": model_id,
            "canonical_model": canonical_model_id(model_id),
            "route_role": str(target["route_role"]),
            "input_scope": str(target["input_scope"]),
            "model_status": profile.status if profile else "unknown",
            "cost_tier": profile.cost_tier if profile else "unknown",
            "latency_tier": profile.latency_tier if profile else "unknown",
            "capabilities": list(profile.capabilities) if profile else [],
            "best_for": list(profile.best_for) if profile else [],
            "input_usd_per_million_tokens": profile.input_usd_per_million_tokens if profile else None,
            "batch_input_usd_per_million_tokens": target["batch_input_usd_per_million_tokens"],
            "pricing_status": pricing_status,
            "budget_mode": budget.budget_mode,
            "max_cost_tier": budget.max_cost_tier,
            "is_known_model": budget.is_known_model,
            "is_over_budget": budget.is_over_budget,
            "requires_operator_review": budget.requires_operator_review or budget.is_over_budget,
            "default_allowed_without_review": bool(target["default_allowed_without_review"])
            and not budget.is_over_budget
            and pricing_status == "priced"
            and (profile.status if profile else "unknown") == "stable",
            "recommended_policy": str(target["recommended_policy"]),
            "release_action": "ready_for_text_embedding_default"
            if not budget.is_over_budget and str(target["route_role"]).startswith("cheap_first")
            else "explicit_review_before_default",
        }

    def _route_row(self, target: dict[str, Any]) -> dict[str, Any]:
        default_model = str(target.get("default_model") or task_default_model("embedding"))
        budget = model_budget_decision(default_model, task=str(target["task"]))
        profile = model_profile(default_model)
        reason_codes: list[str] = []
        if profile is None:
            reason_codes.append("model_not_in_local_catalog")
        if budget.is_over_budget:
            reason_codes.append("over_embedding_budget")
        if str(target["route_mode"]).startswith("explicit"):
            reason_codes.append("explicit_multimodal_review_required")
        route_status = "review_required" if reason_codes else "ready"
        return {
            "id": str(target["id"]),
            "task": str(target["task"]),
            "display_name": str(target["display_name"]),
            "route_mode": str(target["route_mode"]),
            "default_model": default_model,
            "canonical_model": canonical_model_id(default_model),
            "budget_mode": budget.budget_mode,
            "cost_tier": profile.cost_tier if profile else "unknown",
            "expected_inputs": [str(item) for item in target["expected_inputs"]],
            "release_policy": str(target["release_policy"]),
            "route_status": route_status,
            "reason_codes": reason_codes or ["embedding_preflight_ready"],
            "next_action": self._route_action(route_status, reason_codes),
        }

    def _checks(self, embedding_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        default_row = next(
            (row for row in embedding_rows if row["model_id"] == task_default_model("embedding")),
            None,
        )
        multimodal_rows = [row for row in embedding_rows if row["input_scope"] != "text"]
        review_routes = [row["id"] for row in route_rows if row["route_status"] == "review_required"]
        return [
            {
                "id": "embedding-default-cataloged",
                "status": "pass" if default_row and default_row["is_known_model"] else "fail",
                "reason": "The embedding task default must resolve to a local Gemini embedding catalog row.",
                "evidence": [task_default_model("embedding")],
            },
            {
                "id": "text-embedding-cheap-first",
                "status": "pass" if default_row and default_row["default_allowed_without_review"] else "fail",
                "reason": "The text embedding default must be stable, priced, and within the lowest-tier embedding budget.",
                "evidence": [default_row["model_id"]] if default_row else ["missing_embedding_default"],
            },
            {
                "id": "multimodal-embedding-review-boundary",
                "status": "warn" if multimodal_rows else "fail",
                "reason": "Multimodal embedding remains explicit review before route or default promotion.",
                "evidence": [row["model_id"] for row in multimodal_rows] or ["missing_multimodal_embedding_candidate"],
            },
            {
                "id": "embedding-route-preflight-inventory",
                "status": "warn" if review_routes else "pass",
                "reason": "Text embedding routes are ready for preflight, while multimodal evidence indexing stays review-only.",
                "evidence": review_routes or [row["id"] for row in route_rows],
            },
            {
                "id": "metadata-only-boundary",
                "status": "pass",
                "reason": "This preflight does not call providers, gateways, models, indexes, databases, or write configuration.",
                "evidence": ["gateway_called:false", "network_called:false", "index_written:false"],
            },
        ]

    def _route_action(self, route_status: str, reason_codes: list[str]) -> str:
        if route_status == "ready":
            return "Use the cheap text embedding default for metadata-only RAG index preflight planning."
        if "over_embedding_budget" in reason_codes:
            return "Keep the multimodal embedding route explicit-review until modality pricing and index privacy rules pass."
        return "Review embedding route metadata before claiming support."

    def _recommended_actions(self, embedding_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]) -> list[str]:
        actions = [
            row["recommended_policy"]
            for row in embedding_rows
            if row["requires_operator_review"] or not row["default_allowed_without_review"]
        ]
        actions.extend(row["next_action"] for row in route_rows if row["route_status"] == "review_required")
        actions.append("Keep APP_AI_EMBEDDING_MODEL on gemini-embedding-001 for text-only legal RAG indexing until multimodal review passes.")
        return actions[:8]
