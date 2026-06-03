from __future__ import annotations

import json
import re
from typing import Any

from services.legal_fixture_local_run_package import LegalFixtureLocalRunPackageService


SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{16,}", re.IGNORECASE),
    re.compile(r"APP_AI_KEY\s*=\s*[^,\s;]+", re.IGNORECASE),
)


class LegalFixtureResponseNormalizerService:
    """Normalize local gateway responses into fixture smoke/run-report payloads."""

    def __init__(self, package_service: LegalFixtureLocalRunPackageService | None = None) -> None:
        self.package_service = package_service or LegalFixtureLocalRunPackageService()

    def template(self) -> dict[str, Any]:
        package = self.package_service.build_package(1)
        fixture_id = package["request_files"][0]["fixture_id"] if package["request_files"] else "fixture-service-agreement-small"
        model = package["request_files"][0]["model"] if package["request_files"] else "gemini-2.5-flash-lite"
        return {
            "status": "ready",
            "method": {
                "type": "local-fixture-response-normalizer-template",
                "notes": [
                    "Paste local gateway response JSON after a manual local-run-package request.",
                    "The normalizer extracts choices[0].message.content, redacts secret-like values, and returns smoke/run-report payloads.",
                    "Do not include Authorization headers, API keys, request prompts, client documents, or committed raw output files.",
                ],
            },
            "payload_shape": {
                "responses": {
                    fixture_id: {
                        "phase": "cheap_first",
                        "model": model,
                        "http_status": 200,
                        "latency_ms": 1200,
                        "estimated_cost_usd": package["request_files"][0].get("estimated_request_cost_usd")
                        if package["request_files"]
                        else None,
                        "gateway_response": {
                            "model": model,
                            "choices": [
                                {
                                    "message": {
                                        "content": json.dumps(
                                            {
                                                "fixture_id": fixture_id,
                                                "route": "fast",
                                                "release_decision": "warn",
                                                "route_reason": "local smoke run",
                                            },
                                            ensure_ascii=False,
                                        )
                                    }
                                }
                            ],
                        },
                    }
                }
            },
            "validation_command": "python -m pytest tests/test_legal_fixture_response_normalizer.py tests/test_legal_fixture_local_run_package.py -q",
        }

    def normalize(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        rows = self._response_rows(payload)
        known_fixtures = self._known_fixture_ids()
        normalized_rows = [self._normalize_row(fixture_id, row, known_fixtures) for fixture_id, row in rows]
        observations = {
            row["fixture_id"]: row["observation"]
            for row in normalized_rows
            if row["observation"] is not None
        }
        run_metadata = {
            row["fixture_id"]: row["run_metadata"]
            for row in normalized_rows
            if row["run_metadata"] is not None
        }
        checks = [check for row in normalized_rows for check in row["checks"]]
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        return {
            "status": "fail" if blocking else ("warn" if warnings else "ready"),
            "method": {
                "type": "local-fixture-response-normalizer",
                "notes": [
                    "Normalizes supplied response objects only; it never calls NewAPI, Gemini, or app AI endpoints.",
                    "Returns fixture-smoke observations and fixture-run-report payloads without gateway headers or full response envelopes.",
                    "Secret-like values are redacted before any output text is returned.",
                ],
            },
            "summary": {
                "response_count": len(rows),
                "normalized_observation_count": len(observations),
                "run_metadata_count": len(run_metadata),
                "known_fixture_count": sum(1 for row in normalized_rows if row["known_fixture"]),
                "parsed_json_content_count": sum(1 for row in normalized_rows if row["json_content_parsed"]),
                "redacted_response_count": sum(1 for row in normalized_rows if row["redacted"]),
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
            },
            "observations": observations,
            "run_report_payload": {
                "observations": observations,
                "run_metadata": run_metadata,
            },
            "response_summaries": [
                {
                    "fixture_id": row["fixture_id"],
                    "known_fixture": row["known_fixture"],
                    "http_status": row["http_status"],
                    "model": row["model"],
                    "route": (row["observation"] or {}).get("route"),
                    "content_length": row["content_length"],
                    "json_content_parsed": row["json_content_parsed"],
                    "redacted": row["redacted"],
                    "status": row["status"],
                }
                for row in normalized_rows
            ],
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(blocking, warnings, observations),
            "privacy_note": (
                "This response omits gateway headers, request prompts, and full response envelopes. "
                "Do not commit normalized model output; use it only to submit fixture-smoke and run-report payloads."
            ),
        }

    def _response_rows(self, payload: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        responses = payload.get("responses")
        if isinstance(responses, dict):
            return [
                (str(fixture_id), row if isinstance(row, dict) else {"gateway_response": row})
                for fixture_id, row in responses.items()
            ]
        if isinstance(responses, list):
            rows = []
            for index, row in enumerate(responses, start=1):
                if not isinstance(row, dict):
                    continue
                fixture_id = _text(row.get("fixture_id") or row.get("id") or f"response-{index}")
                rows.append((fixture_id, row))
            return rows
        fixture_id = _text(payload.get("fixture_id") or payload.get("id") or "")
        if fixture_id:
            return [(fixture_id, payload)]
        return []

    def _known_fixture_ids(self) -> set[str]:
        package = self.package_service.build_package(4)
        return {row["fixture_id"] for row in package["request_files"]}

    def _normalize_row(
        self,
        fixture_id: str,
        row: dict[str, Any],
        known_fixtures: set[str],
    ) -> dict[str, Any]:
        gateway_response = row.get("gateway_response", row.get("response", row))
        content = self._extract_content(gateway_response)
        redacted_content, redacted = self._redact(content)
        parsed = self._parse_json_object(redacted_content)
        route = _text(row.get("route") or parsed.get("route") or "")
        http_status = _safe_int(row.get("http_status") or _dict(gateway_response).get("status_code"), None)
        model = _text(row.get("model") or _dict(gateway_response).get("model") or "")
        observation = None
        run_metadata = None
        if redacted_content:
            observation = {
                "route": route,
                "output_text": redacted_content,
                "structured_outputs": parsed,
            }
            run_metadata = {
                "phase": _text(row.get("phase")) or "cheap_first",
                "model": model,
                "estimated_cost_usd": _safe_float(row.get("estimated_cost_usd")),
                "http_status": http_status,
                "latency_ms": _safe_int(row.get("latency_ms"), None),
                "json_content_parsed": bool(parsed),
                "redacted": redacted,
            }
        checks = self._checks(
            fixture_id=fixture_id,
            known_fixture=fixture_id in known_fixtures,
            content=redacted_content,
            route=route,
            http_status=http_status,
            redacted=redacted,
        )
        status = "fail" if any(check["status"] == "fail" for check in checks) else (
            "warn" if any(check["status"] == "warn" for check in checks) else "ready"
        )
        return {
            "fixture_id": fixture_id,
            "known_fixture": fixture_id in known_fixtures,
            "http_status": http_status,
            "model": model,
            "content_length": len(redacted_content),
            "json_content_parsed": bool(parsed),
            "redacted": redacted,
            "observation": observation,
            "run_metadata": run_metadata,
            "checks": checks,
            "status": status,
        }

    def _extract_content(self, value: Any) -> str:
        if isinstance(value, str):
            return value.strip()
        if not isinstance(value, dict):
            return ""
        direct = value.get("content") or value.get("output_text") or value.get("text")
        if direct:
            return self._content_to_text(direct)
        choices = value.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0] if isinstance(choices[0], dict) else {}
            message = first.get("message") if isinstance(first.get("message"), dict) else {}
            delta = first.get("delta") if isinstance(first.get("delta"), dict) else {}
            return self._content_to_text(message.get("content") or delta.get("content") or first.get("text"))
        return ""

    def _content_to_text(self, value: Any) -> str:
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            parts = []
            for item in value:
                if isinstance(item, dict):
                    parts.append(_text(item.get("text") or item.get("content")))
                else:
                    parts.append(_text(item))
            return "\n".join(part for part in parts if part)
        return _text(value)

    def _parse_json_object(self, content: str) -> dict[str, Any]:
        if not content:
            return {}
        try:
            parsed = json.loads(content)
        except (TypeError, json.JSONDecodeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _redact(self, content: str) -> tuple[str, bool]:
        redacted = content
        changed = False
        for pattern in SECRET_PATTERNS:
            redacted, count = pattern.subn("[redacted-secret]", redacted)
            changed = changed or count > 0
        return redacted, changed

    def _checks(
        self,
        *,
        fixture_id: str,
        known_fixture: bool,
        content: str,
        route: str,
        http_status: int | None,
        redacted: bool,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": f"{fixture_id}:known-fixture",
                "status": "pass" if known_fixture else "warn",
                "reason": "Fixture ID exists in the local run package."
                if known_fixture
                else "Fixture ID is not in the bundled local run package.",
            },
            {
                "id": f"{fixture_id}:content-present",
                "status": "pass" if content else "fail",
                "reason": "Gateway message content was extracted."
                if content
                else "No choices[0].message.content, content, or output_text field was found.",
            },
            {
                "id": f"{fixture_id}:http-status",
                "status": "pass" if http_status is None or 200 <= http_status < 300 else "warn",
                "reason": "HTTP status is successful or was omitted."
                if http_status is None or 200 <= http_status < 300
                else f"HTTP status {http_status} should be reviewed before scoring.",
            },
            {
                "id": f"{fixture_id}:route-present",
                "status": "pass" if route else "warn",
                "reason": "A route was supplied or parsed from JSON content."
                if route
                else "No route was supplied; fixture smoke route_match may score zero.",
            },
            {
                "id": f"{fixture_id}:secret-redaction",
                "status": "warn" if redacted else "pass",
                "reason": "Secret-like text was redacted from normalized output."
                if redacted
                else "No secret-like text was detected in extracted content.",
            },
        ]

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        observations: dict[str, Any],
    ) -> list[str]:
        if blocking:
            return [
                "Fix missing response content before posting observations to fixture-smoke.",
                "Confirm you pasted the gateway response object, not the request body or headers.",
            ]
        actions = []
        if observations:
            actions.append("Post run_report_payload.observations to /fixture-smoke.")
            actions.append("Post run_report_payload to /fixture-run-report and /fixture-evidence-bundle.")
        if warnings:
            actions.append("Review warnings before using the run as release-readiness evidence.")
        if not actions:
            actions.append("Submit at least one local gateway response to normalize.")
        return actions


def _safe_int(value: Any, default: int | None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return round(max(0.0, float(value)), 8)
    except (TypeError, ValueError):
        return None


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
