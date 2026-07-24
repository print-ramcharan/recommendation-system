from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.api.db.database import get_db
from services.api.db.repository import ExclusionRepository
from services.api.schemas.exclusion import ExclusionCreate, ExclusionResponse

router = APIRouter(prefix="/users", tags=["exclusions"])

@router.post("/{user_id}/exclusions", response_model=ExclusionResponse)
async def mute_user_category(
    user_id: int,
    payload: ExclusionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Mutes a specific article category topic for a user profile."""
    exclusion_repo = ExclusionRepository(db)
    saved = await exclusion_repo.create_exclusion(user_id=user_id, category=payload.category)
    return ExclusionResponse.model_validate(saved)

@router.delete("/{user_id}/exclusions/{category}")
async def unmute_user_category(
    user_id: int,
    category: str,
    db: AsyncSession = Depends(get_db)
):
    """Unmutes a previously muted category topic for a user profile."""
    exclusion_repo = ExclusionRepository(db)
    success = await exclusion_repo.delete_exclusion(user_id=user_id, category=category)
    if not success:
        raise HTTPException(status_code=404, detail="Category exclusion record not found.")
    return {"message": "Category successfully unmuted.", "user_id": user_id, "category": category}

@router.get("/{user_id}/exclusions", response_model=list[str])
async def get_muted_categories(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves all currently muted categories for a designated user profile."""
    exclusion_repo = ExclusionRepository(db)
    return await exclusion_repo.get_user_exclusions(user_id=user_id)
