from services.api.models.event import Event
from services.api.models.article import Article
from services.api.db.repository import UserRepository, ArticleRepository, EventRepository
from services.api.schemas.event import EventCreate
from services.streaming.producer import publish_event


class EventService:
    def __init__(self, event_repo: EventRepository):
        self.event_repo = event_repo

    async def log_event(self, event: Event) -> Event:
        return await self.event_repo.create_event(event)

    async def ingest_user_event(self, event_in: EventCreate):
        """Orchestrates relational storage ingestion and broadcasts to the streaming queue."""
        # A. Commit to PostgreSQL to maintain source-of-truth metadata audit logs
        new_event = await self.event_repo.create(event_in)
        
        # B. Unpack model fields into a serialization-ready dictionary payload
        event_payload = {
            "event_id": new_event.event_id,
            "user_id": new_event.user_id,
            "article_id": new_event.article_id,
            "event_type": new_event.event_type,
            "timestamp": str(new_event.timestamp) if hasattr(new_event, 'timestamp') else None
        }

        # C. Intercept and dispatch to the Kafka event message broker
        try:
            publish_event(event_payload)
        except Exception as e:
            # Resilient safety boundary: Never crash an active client API response 
            # if the broker backplane experiences temporary network hiccups.
            print(f"⚠️ Ingestion boundary fallback: Kafka publish step errored: {e}")

        return new_event
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