from fastapi import APIRouter
from app.api.endpoints import query, user, consent

router = APIRouter()

# Include the query endpoint router
router.include_router(query.router, tags=["query"])

# Include the user endpoint router
router.include_router(user.router, prefix="/user", tags=["user"])

# Include the consent endpoint router
router.include_router(consent.router, prefix="/consent", tags=["consent"])

@router.get("/health")
async def health_check():
    return {"status": "healthy"}