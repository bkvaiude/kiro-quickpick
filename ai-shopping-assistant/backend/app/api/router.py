from fastapi import APIRouter
from app.api.endpoints import query, user, consent, health, maintenance

router = APIRouter()

# Include the query endpoint router
router.include_router(query.router, tags=["query"])

# Include the user endpoint router
router.include_router(user.router, prefix="/user", tags=["user"])

# Include the consent endpoint router
router.include_router(consent.router, prefix="/consent", tags=["consent"])

# Include the health endpoint router
router.include_router(health.router, prefix="/health", tags=["health"])

# Include the maintenance endpoint router
router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])

# Include credits endpoint (accessible at /credits/status)
from fastapi import APIRouter as SubRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.middleware.auth import get_optional_user
from app.middleware.credit_middleware import get_credit_status
from app.database.manager import get_db_session
from app.middleware.database_error_handlers import handle_database_errors
from typing import Dict, Any

credits_router = SubRouter()

@credits_router.get("/status")
@handle_database_errors
async def get_credit_status_endpoint(
    request: Request, 
    user: Dict[str, Any] = Depends(get_optional_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get credit status for the current user (authenticated or guest)
    """
    return await get_credit_status(request, user, session)

router.include_router(credits_router, prefix="/credits", tags=["credits"])