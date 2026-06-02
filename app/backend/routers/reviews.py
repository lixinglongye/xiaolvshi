from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/entities/reviews", tags=["reviews"])


def _legacy_disabled() -> None:
    raise HTTPException(
        status_code=410,
        detail="Legacy reviews API is disabled. Use /api/v1/deep-review/reports endpoints.",
    )


@router.api_route("", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def reviews_root_disabled():
    _legacy_disabled()


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def reviews_path_disabled(path: str):
    _ = path
    _legacy_disabled()
