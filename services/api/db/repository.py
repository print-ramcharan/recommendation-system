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
    pass