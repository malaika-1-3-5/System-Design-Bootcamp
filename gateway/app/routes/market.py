"""Market Price proxy routes."""

from fastapi import APIRouter, Depends, Request, Query
from app.users import current_active_user
from shared.models.user import User

router = APIRouter()


@router.get("/market-prices")
async def get_market_prices(
    request: Request,
    crop: str = Query(..., description="Crop name"),
    state: str = Query(None, description="State name"),
    current_user: User = Depends(current_active_user),
):
    """Fetch current mandi prices for a crop."""
    client = request.app.state.http_client
    from app.config import get_gateway_settings
    settings = get_gateway_settings()

    params = {"crop": crop}
    if state:
        params["state"] = state

    response = await client.get(
        f"{settings.MARKET_PRICE_URL}/market-prices",
        params=params,
    )
    return response.json()
