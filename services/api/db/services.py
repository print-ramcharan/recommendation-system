from services.api.models.event import Event
from services.api.models.article import Article
from services.api.db.repository import UserRepository, ArticleRepository, EventRepository


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
        event_repo: EventRepository,
    ):
        self.user_repo = user_repo
        self.article_repo = article_repo
        self.event_repo = event_repo

    async def get_recommendations(self, user_id: int, k: int = 10) -> list[Article]:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return []

        recommended = []
        for interest in user.interests:
            articles = await self.article_repo.get_by_category(
                interest,
                limit=20,
            )
            recommended.extend(articles)

        clicked_ids = set(
            await self.event_repo.get_user_clicked_articles(user_id)
        )

        filtered = [
            article
            for article in recommended
            if article.article_id not in clicked_ids
        ]

        unique_articles = {
            article.article_id: article
            for article in filtered
        }

        return list(unique_articles.values())[:k]