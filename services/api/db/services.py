from services.api.models.event import Event
from services.api.models.article import Article
import math
from services.api.db.repository import UserRepository, ArticleRepository, EventRepository, LatencyRepository, ExclusionRepository, EvaluationRepository
from services.api.models.latency import LatencyProfile
from services.api.models.evaluation import RecommendationMetric
from services.api.schemas.event import EventCreate
from services.streaming.producer import publish_event


class EventService:
    def __init__(self, event_repo: EventRepository):
        self.event_repo = event_repo

    async def log_event(self, event: Event) -> Event:
        return await self.event_repo.create_event(event)

    async def ingest_user_event(self, event_in: EventCreate) -> Event:
        """Orchestrates relational storage ingestion and broadcasts to the streaming queue."""
        # A. Commit to PostgreSQL to maintain source-of-truth metadata audit logs
        db_event = Event(
            user_id=event_in.user_id,
            article_id=event_in.article_id,
            event_type=event_in.event_type,
        )
        new_event = await self.event_repo.create_event(db_event)
        
        # B. Unpack model fields into a serialization-ready dictionary payload
        event_payload = {
            "event_id": str(new_event.event_id),
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
        exclusion_repo: ExclusionRepository | None = None
    ):
        self.user_repo = user_repo
        self.article_repo = article_repo
        self.event_repo = event_repo
        self.exclusion_repo = exclusion_repo

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

        excluded_categories = set()
        if self.exclusion_repo:
            muted = await self.exclusion_repo.get_user_exclusions(user_id)
            excluded_categories = {cat.lower() for cat in muted}

        filtered = [
            article
            for article in recommended
            if article.article_id not in clicked_ids and article.category.lower() not in excluded_categories
        ]

        unique_articles = {
            article.article_id: article
            for article in filtered
        }

        return list(unique_articles.values())[:k]


class AnalyticsService:
    def __init__(
        self,
        user_repo: UserRepository,
        article_repo: ArticleRepository,
        event_repo: EventRepository
    ):
        self.user_repo = user_repo
        self.article_repo = article_repo
        self.event_repo = event_repo

    async def get_summary_analytics(self) -> dict:
        """Aggregates system-wide analytics summary metrics and category CTR breakdown."""
        total_clicks = await self.event_repo.get_total_clicks_count()
        total_users = await self.user_repo.get_total_users_count()
        total_articles = await self.article_repo.get_total_articles_count()
        
        breakdown_tuples = await self.event_repo.get_category_click_breakdown()
        
        category_breakdown = []
        for cat, cnt in breakdown_tuples:
            pct = (cnt / total_clicks * 100.0) if total_clicks > 0 else 0.0
            category_breakdown.append({
                "category": cat,
                "click_count": cnt,
                "percentage": round(pct, 2)
            })
            
        return {
            "total_clicks": total_clicks,
            "total_users": total_users,
            "total_articles": total_articles,
            "category_breakdown": category_breakdown
        }


class ProfilingService:
    def __init__(self, latency_repo: LatencyRepository):
        self.latency_repo = latency_repo

    async def record_sample(self, route: str, duration_ms: float) -> LatencyProfile:
        """Records an individual execution duration sample."""
        record = LatencyProfile(route=route, duration_ms=duration_ms)
        return await self.latency_repo.create_latency_record(record)

    async def get_percentile_latencies(self, route: str) -> dict:
        """Calculates SLA percentage latencies (p95, p99)."""
        durations = await self.latency_repo.get_all_latencies_by_route(route)
        if not durations:
            return {
                "route": route,
                "avg_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
                "total_samples": 0
            }

        sorted_durs = sorted(durations)
        total = len(sorted_durs)
        
        def percentile(p):
            idx = int(round(p * (total - 1)))
            return sorted_durs[idx]

        return {
            "route": route,
            "avg_ms": round(sum(sorted_durs) / total, 2),
            "min_ms": round(sorted_durs[0], 2),
            "max_ms": round(sorted_durs[-1], 2),
            "p95_ms": round(percentile(0.95), 2),
            "p99_ms": round(percentile(0.99), 2),
            "total_samples": total
        }


class EvaluationService:
    def __init__(self, evaluation_repo: EvaluationRepository, event_repo: EventRepository):
        self.evaluation_repo = evaluation_repo
        self.event_repo = event_repo

    def calculate_precision_recall_ndcg(self, recommended_ids: list[int], clicked_ids: list[int], k: int) -> tuple[float, float, float]:
        """Calculates Precision@K, Recall@K, and NDCG@K metrics for binary relevance."""
        rec_k = recommended_ids[:k]
        if not rec_k:
            return 0.0, 0.0, 0.0

        clicked_set = set(clicked_ids)
        if not clicked_set:
            return 0.0, 0.0, 0.0

        hits = [1 if rid in clicked_set else 0 for rid in rec_k]
        hits_count = sum(hits)

        precision = hits_count / k
        recall = hits_count / len(clicked_set)

        dcg = 0.0
        for i, hit in enumerate(hits):
            if hit == 1:
                dcg += 1.0 / math.log2(i + 2)

        idcg = 0.0
        ideal_hits_count = min(k, len(clicked_set))
        for i in range(ideal_hits_count):
            idcg += 1.0 / math.log2(i + 2)

        ndcg = (dcg / idcg) if idcg > 0.0 else 0.0
        return precision, recall, ndcg

    async def evaluate_user_recommendations(
        self, user_id: int, recommended_ids: list[int], k: int = 10
    ) -> RecommendationMetric:
        """Computes evaluation quality metrics for a user profile and logs them in db."""
        clicked_ids = await self.event_repo.get_user_clicked_articles(user_id)
        
        precision, recall, ndcg = self.calculate_precision_recall_ndcg(
            recommended_ids=recommended_ids,
            clicked_ids=clicked_ids,
            k=k
        )

        record = RecommendationMetric(
            user_id=user_id,
            precision_at_k=round(precision, 4),
            recall_at_k=round(recall, 4),
            ndcg_at_k=round(ndcg, 4),
            k=k
        )
        return await self.evaluation_repo.create_metrics_record(record)