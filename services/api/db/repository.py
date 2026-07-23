
from services.api.models.event import Event 
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from services.api.models.article import Article
from services.api.models.user import User
from services.api.models.latency import LatencyProfile


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        stmt = select(User).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_interests(self, user_id: int, interests: dict) -> User | None:
        """Updates interests JSON field for a user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.interests = interests
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_total_users_count(self) -> int:
        """Returns total count of user records in database."""
        stmt = select(func.count(User.user_id))
        result = await self.db.execute(stmt)
        return result.scalar() or 0


class ArticleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_articles_by_ids(self, ids: list[int]) -> list[Article]:
        """Performs a highly optimized batch lookup matching a designated array of primary keys."""
        if not ids:
            return []
        stmt = select(Article).where(Article.article_id.in_(ids))
        result = await self.db.execute(stmt)
        articles = list(result.scalars().all())
        
        # Map objects to guarantee we preserve the precise semantic distance order returned by Qdrant
        id_to_article = {a.article_id: a for a in articles}
        return [id_to_article[i] for i in ids if i in id_to_article]
    async def get_by_id(self, article_id: int) -> Article | None:
        stmt = select(Article).where(Article.article_id == article_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_articles(self, skip: int = 0, limit: int = 100) -> list[Article]:
        stmt = select(Article).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_category(self, category: str, limit: int = 50) -> list[Article]:
        stmt = select(Article).where(Article.category == category).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_total_articles_count(self) -> int:
        """Returns total count of article records in database."""
        stmt = select(func.count(Article.article_id))
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def search_by_tags(self, tags: list[str]) -> list[Article]:
        stmt = select(Article)
        result = await self.db.execute(stmt)
        articles = result.scalars().all()
        return [
            article
            for article in articles
            if any(tag in article.tags for tag in tags)
        ]
class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_event(self, event: Event) -> Event:
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_user_events(self, user_id: int, limit: int = 100) -> list[Event]:
        stmt = (
            select(Event)
            .where(Event.user_id == user_id)
            .order_by(Event.timestamp.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_clicked_articles(self, user_id: int) -> list[int]:
        stmt = (
            select(Event.article_id)
            .where(
                Event.user_id == user_id,
                Event.event_type == "click"
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_article_events(self, article_id: int) -> list[Event]:
        stmt = select(Event).where(Event.article_id == article_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_popular_articles(self, limit: int = 10) -> list[int]:
        """Queries the database for most frequently clicked articles."""
        stmt = (
            select(Event.article_id)
            .where(Event.event_type == "click")
            .group_by(Event.article_id)
            .order_by(func.count(Event.event_id).desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_total_clicks_count(self) -> int:
        """Returns total number of click interactions recorded across system."""
        stmt = select(func.count(Event.event_id)).where(Event.event_type == "click")
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_category_click_breakdown(self) -> list[tuple[str, int]]:
        """Queries category distribution of clicks joined with Article model."""
        stmt = (
            select(Article.category, func.count(Event.event_id))
            .join(Article, Event.article_id == Article.article_id)
            .where(Event.event_type == "click")
            .group_by(Article.category)
            .order_by(func.count(Event.event_id).desc())
        )
        result = await self.db.execute(stmt)
        return list(result.all())


class LatencyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_latency_record(self, record: LatencyProfile) -> LatencyProfile:
        """Persists a new latency sample entry to database."""
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_latency_samples_by_route(self, route: str, limit: int = 100) -> list[LatencyProfile]:
        """Queries recent latency samples registered for a specified endpoint path."""
        stmt = (
            select(LatencyProfile)
            .where(LatencyProfile.route == route)
            .order_by(LatencyProfile.timestamp.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_latencies_by_route(self, route: str) -> list[float]:
        """Queries durations for statistical metrics calculation."""
        stmt = select(LatencyProfile.duration_ms).where(LatencyProfile.route == route)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())