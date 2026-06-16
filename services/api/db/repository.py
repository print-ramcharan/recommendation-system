
from services.api.models.event import Event 
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from services.api.models.article import Article
from services.api.models.user import User


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