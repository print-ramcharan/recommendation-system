from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.api.db.database import get_db
from services.api.db.repository import UserRepository
from services.api.schemas.user import UserInterestsUpdate
from services.cache.redis_client import redis_client

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}/interests")
async def get_user_interests(user_id: int, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User profile records not found.")
    
    interests = user.interests or {}
    return {
        "user_id": user_id,
        "preferred_topics": interests.get("preferred_topics", []) if isinstance(interests, dict) else []
    }

@router.put("/{user_id}/interests")
async def update_user_interests(
    user_id: int, 
    payload: UserInterestsUpdate, 
    db: AsyncSession = Depends(get_db)
):
    repo = UserRepository(db)
    interests_dict = {"preferred_topics": payload.preferred_topics}
    user = await repo.update_interests(user_id, interests_dict)
    
    if not user:
        raise HTTPException(status_code=404, detail="User profile records not found.")
        
    # Invalidate Redis embedding cache
    try:
        redis_client.delete(f"user_embedding:{user_id}")
    except Exception as e:
        print(f"⚠️ Redis cache invalidation error: {e}")
        
    return {
        "status": "success",
        "user_id": user_id,
        "interests": user.interests
    }
