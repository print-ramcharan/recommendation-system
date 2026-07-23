# Simulator Dashboard Features Guide

The Recommendation Engine Simulator at `/dashboard` serves as an interactive playground to test personalization pipelines and background tasks.

## Key Interface Cards

### 1. Personalized Simulator
* **Input Fields**: Takes User ID and recommendation count `k`.
* **Experiment Group**: Visualizes current A/B testing experiment group allocated dynamically based on user ID hashing:
  * **Group A**: Vector search retrieve with freshness & category decay.
  * **Group B**: Heuristic popularity baseline fallback.
  * **Group C**: Neural Collaborative Filtering (NCF) deep model ranking.
* **Latency Chart**: Utilizes Chart.js to render a running line chart tracking the past 10 API requests' response duration in milliseconds.

### 2. User Profile Interests Editor
* **Interests Lookup**: Fetches and displays the user's current preferred topics directly from PostgreSQL on User ID changes.
* **Interests Writer**: Allows updating preferred topics with a comma-separated list.
* **Cache Invalidation**: Automatically purges pre-computed user vectors from the Redis Feature Store, forcing the API to compute updated embeddings on the next personalized simulator request.

### 3. Semantic Search Panel
* **Natural Language Queries**: Leverages the SentenceTransformer model to perform ad-hoc vector similarity query retrievals directly on Qdrant DB points.

### 3. NCF Model Retrainer
* **Training Trigger**: Dispatches training jobs asynchronously using FastAPI BackgroundTasks.
* **Progress Poller**: Polls status from `/ml/status` dynamically detailing the current epoch number and loss value updates.
* **Status Flags**: Displays `IDLE`, `TRAINING`, and `FAILED` states.

### 4. Category Interaction CTR & Metrics
* **Total Counts**: Live counters for total recorded click events, registered user profiles, and published articles.
* **Doughnut Distribution Chart**: Uses Chart.js to visually display the percentage click share across article categories.
* **Real-time Synchronization**: Re-fetches `/analytics/summary` automatically upon dispatching new click interaction events.

### 5. Server-Sent Events (SSE) Live Click Feed
* **Live Broadcasting**: Listens to `/notifications/stream` for real-time EventSource signals.
* **Feed Updates**: Dynamically constructs feed elements for incoming user clicks with active timestamp attributes.
* **Automatic Stat Sync**: Directs other browser simulator sessions to refresh their analytics metrics automatically when a click event is broadcasted.

### 6. Latency SLA Performance Metrics
* **Percentile Aggregations**: Queries `/profiling/stats` to retrieve p95, p99, and average response times in milliseconds.
* **Database Samples**: Dynamically tracks execution samples across the recommendation engine pipeline to compute true SLA compliance benchmarks.
* **Auto-refresh Cycle**: Re-fetches the latest statistics automatically upon completion of recommendation queries.
