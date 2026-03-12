"""Disease Detection proxy routes."""

from fastapi import APIRouter, Depends, UploadFile, File, Request
from app.users import current_active_user
from shared.models.user import User

router = APIRouter()


@router.post("/detect")
async def detect_disease(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(current_active_user),
):
    """Proxy image upload to the Disease Detection service."""
    client = request.app.state.http_client
    from app.config import get_gateway_settings
    settings = get_gateway_settings()

    files = {"file": (file.filename, await file.read(), file.content_type)}
    data = {"farmer_id": str(current_user.id)}

    response = await client.post(
        f"{settings.DISEASE_DETECTION_URL}/detect",
        files=files,
        data=data,
    )
    return response.json()
