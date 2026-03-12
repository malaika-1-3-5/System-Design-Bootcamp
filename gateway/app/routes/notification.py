"""Notification proxy routes."""

from fastapi import APIRouter, Depends, Request
from app.users import current_active_user
from shared.models.user import User

router = APIRouter()


@router.get("/notifications/{farmer_id}")
async def get_notifications(
    farmer_id: str,
    request: Request,
    current_user: User = Depends(current_active_user),
):
    """Fetch notifications for a farmer."""
    client = request.app.state.http_client
    from app.config import get_gateway_settings
    settings = get_gateway_settings()

    response = await client.get(
        f"{settings.NOTIFICATION_URL}/notifications/{farmer_id}",
    )
    return response.json()
