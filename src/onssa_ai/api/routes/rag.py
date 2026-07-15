"""RAG API endpoints."""

from fastapi import APIRouter, HTTPException, status

from onssa_ai.schemas.rag import RagRequest, RagResponse

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/answer", response_model=RagResponse)
async def answer(_request: RagRequest) -> RagResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="RAG dependencies are not wired yet. Implement retrieval/indexing first.",
    )
