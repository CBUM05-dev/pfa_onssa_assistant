"""RAG API endpoints."""

import httpx
from fastapi import APIRouter, HTTPException, status

from onssa_ai.api.dependencies import get_rag_service
from onssa_ai.schemas.rag import RagRequest, RagResponse

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/answer", response_model=RagResponse)
async def answer(request: RagRequest) -> RagResponse:
    try:
        rag_service = get_rag_service()
        return await rag_service.answer(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM provider returned HTTP {exc.response.status_code}.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to reach configured LLM provider.",
        ) from exc
