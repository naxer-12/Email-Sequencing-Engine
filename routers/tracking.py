import base64

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, Response
from jose import jwt

from config import settings
from kafka.producer import produce_event

router = APIRouter(prefix="/t", tags=["tracking"])

# Tiny 1x1 transparent GIF
PIXEL = base64.b64decode(b"R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")


def create_tracking_token(enrollment_id: int, step_id: int) -> str:
    """Create a JWT token that encodes the tracking data"""
    payload = {
        "eid": enrollment_id,
        "sid": step_id,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_tracking_token(token: str) -> dict:
    """Decode and verify the token"""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except:
        return None


@router.get("/open/{token}")
async def track_open(token: str):
    """Tracking pixel endpoint — called when email is opened"""
    data = decode_tracking_token(token)
    print(f"Decoded tracking data: {data}")

    if not data:
        return Response(content=PIXEL, media_type="image/gif")

    # Emit event to Kafka
    produce_event("email.opened", data["eid"], data["sid"])

    # Return the pixel (1x1 GIF)
    return Response(content=PIXEL, media_type="image/gif")


@router.get("/click")
async def track_click(token: str, url: str):
    """Link click redirect — called when user clicks a link"""
    data = decode_tracking_token(token)
    if data:
        produce_event("email.clicked", data["eid"], data["sid"])

    return RedirectResponse(url=url, status_code=302)
