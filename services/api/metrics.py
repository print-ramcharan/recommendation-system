from prometheus_client import Counter, Histogram

# Measure end-to-end vector pipeline latency distributions
RECOMMENDATION_LATENCY = Histogram(
    name="recommendation_latency_seconds",
    documentation="Detailed pipeline execution latency for personalized recommendations",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5)
)

# Operational Feature Store caching efficiency metrics
CACHE_HITS = Counter(
    name="redis_cache_hits_total",
    documentation="Total count of hits against the Redis Feature Store"
)

CACHE_MISSES = Counter(
    name="redis_cache_misses_total",
    documentation="Total count of misses against the Redis Feature Store forcing re-computation"
)