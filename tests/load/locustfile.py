import random
from locust import HttpUser, task, between

class RecommendationUser(HttpUser):
    # Simulated pacing gap between user actions
    wait_time = between(1.0, 3.0)

    def on_start(self):
        """Runs automatically when a virtual user wakes up."""
        # Hardcoded array mapping your database's valid target IDs
        self.test_user_ids = [221186]
        self.test_article_ids = [610304, 850269, 657579]

    @task(3)
    def personalized_recommendations(self):
        """Simulates feed navigations by cleanly interpolating dynamic numerical IDs."""
        user_id = random.choice(self.test_user_ids)
        
        # CRITICAL: The 'f' prefix forces python to insert the integer variable!
        self.client.get(
            f"/recommendations/personalized/{user_id}?k=5",
            name="/recommendations/personalized/{user_id}"
        )

    @task(1)
    def semantic_search(self):
        """Simulates deep context vector similarity searches."""
        article_id = random.choice(self.test_article_ids)
        
        # CRITICAL: The 'f' prefix forces python to insert the integer variable!
        self.client.get(
            f"/articles/{article_id}/similar?k=5",
            name="/articles/{article_id}/similar"
        )