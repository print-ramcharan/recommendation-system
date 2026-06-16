from sqlalchemy.ext.asyncio import AsyncSession
# Note: You'll want to import your User, Article, and Event SQLAlchemy models here later

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


class ArticleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session