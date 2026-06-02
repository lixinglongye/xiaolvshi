import json
from typing import Any, Dict, Optional

from fastapi import HTTPException
from pydantic import BaseModel


def parse_query_param(query: Optional[str]) -> Optional[Dict[str, Any]]:
    if not query:
        return None
    try:
        parsed = json.loads(query)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid query JSON format") from exc
    if parsed is None:
        return None
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="Query JSON must be an object")
    return parsed


def partial_update_data(data: BaseModel) -> Dict[str, Any]:
    return {key: value for key, value in data.model_dump().items() if value is not None}
