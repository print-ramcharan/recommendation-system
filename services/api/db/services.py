from asyncio import Event

from .repository import UserRepository, ArticleRepository, EventRepository

class EventService:
    def __init__(self, event_repo: EventRepository):
        self.event_repo = event_repo

    async def log_event(self, event: Event) -> Event:
        return await self.event_repo.create_event(event)

    async def get_user_history(self, user_id: int, limit: int = 100) -> list[Event]:
        return await self.event_repo.get_user_events(
            user_id=user_id,
            limit=limit,
        )

    async def get_clicked_articles(self, user_id: int) -> list[int]:
        return await self.event_repo.get_user_clicked_articles(user_id)
    
class RecommendationService:
    def __init__(
        self, 
        user_repo: UserRepository, 
        article_repo: ArticleRepository, 
        event_repo: EventRepository
    ):
        self.user_repo = user_repo
        self.article_repo = article_repo
        self.event_repo = event_repo