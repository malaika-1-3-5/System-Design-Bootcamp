"""Irrigation proxy routes."""

from fastapi import APIRouter, Depends, Request, Query
from app.users import current_active_user
from shared.models.user import User

router = APIRouter()


@router.get("/irrigation")
async def get_irrigation(
    request: Request,
    crop: str = Query(..., description="Crop type"),
    soil_moisture: float = Query(None, description="Current soil moisture %"),
    temperature: float = Query(None, description="Current temperature °C"),
    growth_stage: str = Query(None, description="Growth stage"),
    current_user: User = Depends(current_active_user),
):
    """Fetch irrigation recommendation for given conditions."""
    client = request.app.state.http_client
    from app.config import get_gateway_settings
    settings = get_gateway_settings()

    params = {"crop": crop}
    if soil_moisture is not None:
        params["soil_moisture"] = soil_moisture
    if temperature is not None:
        params["temperature"] = temperature
    if growth_stage is not None:
        params["growth_stage"] = growth_stage

    response = await client.get(
        f"{settings.IRRIGATION_URL}/irrigation",
        params=params,
    )
    return response.json()
