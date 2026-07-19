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

### 2. Semantic Search Panel
* **Natural Language Queries**: Leverages the SentenceTransformer model to perform ad-hoc vector similarity query retrievals directly on Qdrant DB points.

### 3. NCF Model Retrainer
* **Training Trigger**: Dispatches training jobs asynchronously using FastAPI BackgroundTasks.
* **Progress Poller**: Polls status from `/ml/status` dynamically detailing the current epoch number and loss value updates.
* **Status Flags**: Displays `IDLE`, `TRAINING`, and `FAILED` states.
