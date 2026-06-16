from .repository import UserRepository, ArticleRepository, EventRepository

class EventService:
    def __init__(
        self, 
        event_repo: EventRepository, 
        user_repo: UserRepository, 
        article_repo: ArticleRepository
    ):
        self.event_repo = event_repo
        self.user_repo = user_repo
        self.article_repo = article_repo


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