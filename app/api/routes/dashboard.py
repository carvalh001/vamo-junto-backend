from fastapi import APIRouter, Depends, Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.deps import get_current_user
from app.services.db_service import get_user_stats
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/stats")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_dashboard_stats(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard statistics for current user"""
    try:
        stats = get_user_stats(current_user["id"])
        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics. Please try again."
        )

