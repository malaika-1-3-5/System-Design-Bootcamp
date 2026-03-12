"""AI Advisory proxy routes."""

from fastapi import APIRouter, Depends, Request, Query
from app.users import current_active_user
from shared.models.user import User

router = APIRouter()


@router.get("/advisory/search")
async def search_knowledge_base(
    request: Request,
    query: str = Query(..., description="Search query e.g. 'tomato late blight treatment'"),
    crop: str = Query(None, description="Filter by crop (e.g. Tomato, Potato)"),
    top_k: int = Query(3, ge=1, le=10, description="Number of results to return"),
    current_user: User = Depends(current_active_user),
):
    """Search the disease knowledge base in Qdrant."""
    client = request.app.state.http_client
    from app.config import get_gateway_settings
    settings = get_gateway_settings()

    params = {"query": query, "top_k": top_k}
    if crop:
        params["crop"] = crop

    response = await client.get(
        f"{settings.AI_ADVISORY_URL}/advisory/search",
        params=params,
    )
    return response.json()


@router.get("/advisory/{upload_id}")
async def get_advisory(
    upload_id: str,
    request: Request,
    current_user: User = Depends(current_active_user),
):
    """Fetch AI-generated advisory for a given upload."""
    client = request.app.state.http_client
    from app.config import get_gateway_settings
    settings = get_gateway_settings()

    response = await client.get(
        f"{settings.AI_ADVISORY_URL}/advisory/{upload_id}",
        params={"farmer_id": str(current_user.id)},
    )
    return response.json()
