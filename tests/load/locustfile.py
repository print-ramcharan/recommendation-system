import random
from locust import HttpUser, task, between
from sqlalchemy import create_engine, text

class RecommendationUser(HttpUser):
    # Simulated pacing gap between user actions
    wait_time = between(1.0, 3.0)

    def on_start(self):
        """Runs automatically when a virtual user wakes up."""
        try:
            # Query the local PostgreSQL instance to gather actual valid IDs
            db_url = "postgresql://postgres:postgres@localhost:5432/recommendation_db"
            engine = create_engine(db_url)
            with engine.connect() as conn:
                user_rows = conn.execute(text("SELECT user_id FROM users LIMIT 100")).fetchall()
                article_rows = conn.execute(text("SELECT article_id FROM articles LIMIT 100")).fetchall()
                
            self.test_user_ids = [row[0] for row in user_rows] if user_rows else [221186]
            self.test_article_ids = [row[0] for row in article_rows] if article_rows else [610304, 850269, 657579]
            print(f"Loaded {len(self.test_user_ids)} users and {len(self.test_article_ids)} articles dynamically.")
        except Exception as e:
            print(f"⚠️ Failed to dynamically load IDs from DB: {e}. Falling back to default list.")
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