"""Search API endpoints."""

from fastapi import APIRouter, HTTPException, status

from onssa_ai.schemas.retrieval import RetrievalRequest

router = APIRouter(prefix="/search", tags=["search"])


@router.post("")
async def search(_request: RetrievalRequest) -> dict[str, str]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Qdrant retrieval is not implemented yet.",
    )
