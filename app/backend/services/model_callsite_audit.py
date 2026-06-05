from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GenTxtCallsite:
    file: str
    line: int
    function: str
    has_task: bool
    has_model: bool
    status: str
    reason: str

    def to_api(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "function": self.function,
            "has_task": self.has_task,
            "has_model": self.has_model,
            "status": self.status,
            "reason": self.reason,
        }


class ModelCallsiteAuditService:
    """Static audit for GenTxtRequest runtime routing coverage."""

    def __init__(self, backend_root: Path | None = None) -> None:
        self.backend_root = backend_root or Path(__file__).resolve().parents[1]

    def audit(self) -> dict[str, Any]:
        callsites = self._collect_callsites()
        failing = [item for item in callsites if item.status == "fail"]
        warnings = [item for item in callsites if item.status == "warn"]

        return {
            "status": "fail" if failing else ("warn" if warnings else "pass"),
            "method": {
                "type": "static-python-ast",
                "scope": "app/backend/services",
                "notes": [
                    "Scans service-layer GenTxtRequest call sites for explicit task routing metadata.",
                    "Does not read prompts, documents, API keys, environment variables, or runtime model responses.",
                    "Complements automatic task inference by making critical business flows explicitly auditable.",
                ],
            },
            "summary": {
                "callsite_count": len(callsites),
                "explicit_task_count": sum(1 for item in callsites if item.has_task),
                "missing_task_count": sum(1 for item in callsites if not item.has_task),
                "with_model_count": sum(1 for item in callsites if item.has_model),
                "fail_count": len(failing),
                "warn_count": len(warnings),
            },
            "callsites": [item.to_api() for item in callsites],
            "recommended_actions": self._recommended_actions(failing, warnings),
        }

    def _collect_callsites(self) -> list[GenTxtCallsite]:
        services_dir = self.backend_root / "services"
        callsites: list[GenTxtCallsite] = []
        for path in sorted(services_dir.rglob("*.py")):
            if path.name.startswith("test_"):
                continue
            rel_path = _relative(path, self.backend_root)
            try:
                source = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError) as exc:
                callsites.append(
                    GenTxtCallsite(
                        file=rel_path,
                        line=0,
                        function="<parse>",
                        has_task=False,
                        has_model=False,
                        status="fail",
                        reason=f"Could not read file for GenTxtRequest audit: {exc}.",
                    )
                )
                continue
            if "GenTxtRequest" not in source:
                continue
            try:
                tree = ast.parse(source, filename=str(path))
            except SyntaxError as exc:
                callsites.append(
                    GenTxtCallsite(
                        file=rel_path,
                        line=exc.lineno or 0,
                        function="<parse>",
                        has_task=False,
                        has_model=False,
                        status="fail",
                        reason=f"Could not parse file for GenTxtRequest audit: {exc.msg}.",
                    )
                )
                continue

            parents = _parent_map(tree)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and _call_name(node.func) == "GenTxtRequest":
                    keywords = {keyword.arg for keyword in node.keywords if keyword.arg}
                    has_task = "task" in keywords
                    has_model = "model" in keywords
                    callsites.append(
                        GenTxtCallsite(
                            file=rel_path,
                            line=getattr(node, "lineno", 0),
                            function=_enclosing_function(node, parents),
                            has_task=has_task,
                            has_model=has_model,
                            status="pass" if has_task else "fail",
                            reason="Call site provides explicit task routing metadata."
                            if has_task
                            else "Call site relies only on automatic task inference; add task=... for auditable routing.",
                        )
                    )
        callsites.sort(key=lambda item: (item.file, item.line))
        return callsites

    def _recommended_actions(
        self,
        failing: list[GenTxtCallsite],
        warnings: list[GenTxtCallsite],
    ) -> list[str]:
        if failing:
            return [
                f"Add explicit task routing metadata to {item.file}:{item.line} in {item.function}."
                for item in failing[:10]
            ]
        if warnings:
            return [
                f"Review warning at {item.file}:{item.line} in {item.function}."
                for item in warnings[:10]
            ]
        return ["All service-layer GenTxtRequest call sites provide explicit task metadata."]


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _enclosing_function(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
    return "<module>"


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
