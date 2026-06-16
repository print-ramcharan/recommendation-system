import random
from locust import HttpUser, task, between

class RecommendationUser(HttpUser):
    # Simulate users waiting between 1 to 3 seconds between actions
    wait_time = between(1.0, 3.0)

    def on_start(self):
        """Runs automatically when a virtual user instantiates to seed targets."""
        # Seeding target pools that mimic your generated relational dataset profiles
        self.test_user_ids = [221186, 100123, 345678, 554321, 889900]
        self.test_article_ids = [610304, 850269, 657579, 460864, 364949]

    @task(3)
    def personalized_recommendations(self):
        """Simulates feed navigation requests hitting your cache-centric route (75% weight)."""
        user_id = random.choice(self.test_user_ids)
        self.client.get(
            f"/recommendations/personalized/{user_id}?k=5",
            name="/recommendations/personalized/[user_id]"
        )

    @task(1)
    def semantic_search(self):
        """Simulates deep content searches triggering direct Qdrant index lookups (25% weight)."""
        article_id = random.choice(self.test_article_ids)
        self.client.get(
            f"/articles/{article_id}/similar?k=5",
            name="/articles/[article_id]/similar"
        )