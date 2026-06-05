from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any

from core.config import Settings


@dataclass(frozen=True)
class TemplateModelDefault:
    env_var: str
    settings_attr: str
    task: str
    required_for: str

    def to_api(self) -> dict[str, str]:
        return asdict(self)


TEMPLATE_MODEL_DEFAULTS: tuple[TemplateModelDefault, ...] = (
    TemplateModelDefault("APP_AI_CHEAP_MODEL", "app_ai_cheap_model", "cheap", "cheap-first text baseline"),
    TemplateModelDefault("APP_AI_BALANCED_MODEL", "app_ai_balanced_model", "balanced", "balanced review baseline"),
    TemplateModelDefault("APP_AI_PREMIUM_MODEL", "app_ai_premium_model", "premium", "premium exception baseline"),
    TemplateModelDefault("APP_OCR_MODEL", "app_ocr_model", "ocr", "OCR cheap-first route"),
    TemplateModelDefault("APP_AI_FAST_MODEL", "app_ai_fast_model", "fast", "fast cheap-first route"),
    TemplateModelDefault("APP_AI_CLASSIFIER_MODEL", "app_ai_classifier_model", "classification", "classification cheap-first route"),
    TemplateModelDefault("APP_AI_AGENTIC_MODEL", "app_ai_agentic_model", "agentic", "agentic low-cost Gemini route"),
    TemplateModelDefault(
        "APP_AI_GROUNDED_RESEARCH_MODEL",
        "app_ai_grounded_research_model",
        "grounded-research",
        "grounded research low-cost Gemini route",
    ),
    TemplateModelDefault("APP_AI_REVIEW_MODEL", "app_ai_review_model", "review", "legal review route"),
    TemplateModelDefault("APP_AI_PDF_MODEL", "app_ai_pdf_model", "pdf", "large PDF premium exception route"),
    TemplateModelDefault("APP_AI_IMAGE_MODEL", "app_ai_image_model", "image", "media route"),
)


SOURCE_FILES: dict[str, str] = {
    "env_example": "app/backend/.env.example",
    "readme": "README.md",
    "ai_model_strategy": "docs/AI_MODEL_STRATEGY.md",
}


class ModelDefaultTemplateAuditService:
    """Audit checked-in docs/templates for cheap-first Gemini default drift."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path(__file__).resolve().parents[3]

    def build_audit(self, source_overrides: dict[str, str] | None = None) -> dict[str, Any]:
        source_overrides = source_overrides or {}
        parsed_sources = {
            source_id: self._parse_env_assignments(self._read_source(source_id, source_overrides))
            for source_id in SOURCE_FILES
        }
        rows = [self._row(target, parsed_sources) for target in TEMPLATE_MODEL_DEFAULTS]
        blocking = [row for row in rows if row["status"] == "fail"]

        return {
            "status": "fail" if blocking else "pass",
            "method": {
                "type": "model-default-template-alignment-audit",
                "notes": [
                    "Compares Settings class defaults with checked-in environment examples and public docs.",
                    "Prevents Gemini cheap-first defaults from drifting after model catalog or routing changes.",
                    "Does not read .env, environment variables, API keys, prompts, legal documents, or gateway responses.",
                ],
            },
            "summary": {
                "default_count": len(rows),
                "source_count": len(SOURCE_FILES),
                "aligned_count": sum(1 for row in rows if row["status"] == "pass"),
                "drift_count": len(blocking),
                "missing_value_count": sum(len(row["missing_sources"]) for row in rows),
                "mismatched_value_count": sum(len(row["mismatched_sources"]) for row in rows),
                "agentic_grounded_defaults_visible": self._agentic_grounded_visible(rows),
            },
            "source_files": [
                {"id": source_id, "path": path}
                for source_id, path in SOURCE_FILES.items()
            ],
            "default_targets": [target.to_api() for target in TEMPLATE_MODEL_DEFAULTS],
            "rows": rows,
            "blocking_check_ids": [row["id"] for row in blocking],
            "warning_check_ids": [],
            "recommended_actions": self._recommended_actions(blocking),
            "privacy_boundary": {
                "metadata_only": True,
                "real_env_read": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_returned": False,
                "prompts_included": False,
                "raw_payloads_included": False,
                "model_outputs_included": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_default_template_audit.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_model_catalog.py tests/test_modelops_gemini_cheap_first_coverage_gate.py -q",
            ],
        }

    def _row(self, target: TemplateModelDefault, parsed_sources: dict[str, dict[str, str]]) -> dict[str, Any]:
        expected = self._settings_default(target.settings_attr)
        values = {
            source_id: source_values.get(target.env_var)
            for source_id, source_values in parsed_sources.items()
        }
        missing_sources = [source_id for source_id, value in values.items() if not value]
        mismatched_sources = [
            source_id
            for source_id, value in values.items()
            if value and value != expected
        ]
        status = "fail" if missing_sources or mismatched_sources else "pass"
        return {
            "id": f"default-template-{target.env_var.lower()}",
            "env_var": target.env_var,
            "settings_attr": target.settings_attr,
            "task": target.task,
            "required_for": target.required_for,
            "expected_default": expected,
            "source_values": values,
            "missing_sources": missing_sources,
            "mismatched_sources": mismatched_sources,
            "status": status,
            "reason": self._reason(target, expected, missing_sources, mismatched_sources),
        }

    def _settings_default(self, attr: str) -> str:
        fields = getattr(Settings, "model_fields", None)
        if fields and attr in fields:
            return str(fields[attr].default or "")
        legacy_fields = getattr(Settings, "__fields__", {})
        if attr in legacy_fields:
            return str(legacy_fields[attr].default or "")
        return ""

    def _read_source(self, source_id: str, overrides: dict[str, str]) -> str:
        if source_id in overrides:
            return overrides[source_id]
        path = self.repo_root / SOURCE_FILES[source_id]
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""

    def _parse_env_assignments(self, text: str) -> dict[str, str]:
        values: dict[str, str] = {}
        for match in re.finditer(r"(?m)^\s*([A-Z][A-Z0-9_]+)\s*=\s*([^\r\n#]+?)\s*$", text or ""):
            key, value = match.groups()
            values[key] = value.strip()
        return values

    def _agentic_grounded_visible(self, rows: list[dict[str, Any]]) -> bool:
        targets = {"APP_AI_AGENTIC_MODEL", "APP_AI_GROUNDED_RESEARCH_MODEL"}
        relevant = [row for row in rows if row["env_var"] in targets]
        return len(relevant) == 2 and all(row["status"] == "pass" for row in relevant)

    def _reason(
        self,
        target: TemplateModelDefault,
        expected: str,
        missing_sources: list[str],
        mismatched_sources: list[str],
    ) -> str:
        if missing_sources:
            return f"{target.env_var} is missing from: {', '.join(missing_sources)}."
        if mismatched_sources:
            return f"{target.env_var} should be {expected} in: {', '.join(mismatched_sources)}."
        return f"{target.env_var} is aligned with Settings default {expected}."

    def _recommended_actions(self, blocking: list[dict[str, Any]]) -> list[str]:
        if not blocking:
            return ["Keep Settings defaults, .env.example, README, and AI model strategy docs aligned before changing Gemini defaults."]
        return [
            f"Align {row['env_var']} to {row['expected_default']} in {', '.join([*row['missing_sources'], *row['mismatched_sources']])}."
            for row in blocking[:8]
        ]
