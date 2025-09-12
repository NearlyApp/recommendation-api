from lib.pydantic.requests import RecommendationRequest
from worker.lib.embeddings import embed_data
from worker.lib.opensearch import OpenSearchClient
from worker.lib.pydantic.data_models import DataModel
from pydantic import ValidationError
from cachetools import TTLCache, cached
from datetime import datetime
import json

opensearch_client = OpenSearchClient()
print("OpenSearch client connected")

# short lived cache for embedding candidates based on id
embedding_cache = TTLCache(maxsize=100, ttl=3600)


@cached(embedding_cache)
def get_embedding(candidate_id: str):
    """
    Retrieves the embedding for a given candidate ID from the cache.
    """
    return embedding_cache.get(candidate_id)


def apply_weights(embeddings: list[list[float]], original_data: list[DataModel]) -> list[float]:
    """
    Apply weights according to created_at 
    """
    if not embeddings or not original_data or len(embeddings) != len(original_data):
        return []

    # Parse created_at strings to timestamps
    timestamps = []
    for data in original_data:
        # Handle both string and datetime objects
        dt = datetime.fromisoformat(data.created_at)
        timestamps.append(dt.timestamp())


    # Example: Simple weighting based on recency (newer items get higher weight)
    current_time = max(timestamps) if timestamps else datetime.now().timestamp()
    weights = [
        1 + (timestamp / current_time) if current_time > 0 else 1
        for timestamp in timestamps
    ]

    weighted_embedding = [0.0] * len(embeddings[0])
    total_weight = sum(weights)

    for emb, weight in zip(embeddings, weights):
        for i in range(len(emb)):
            weighted_embedding[i] += emb[i] * (weight / total_weight)

    return weighted_embedding


def handler(event, context):
    try:
        raw_body = event.get("body", "{}")
        body = RecommendationRequest(**json.loads(raw_body))

        # Process the recommendation request using body.candidates and body.location
        # For example, you might call a recommendation engine here
        embeddings = []
        print(f"Processing {len(body.candidates)} candidates")
        print("Generating embeddings for candidates...")
        for candidate in body.candidates:
            embedding = get_embedding(candidate.post_id)
            if embedding:
                print("Cache hit")
                embeddings.append(embedding)
            else:
                print("Cache miss")
                new_embedding = embed_data(candidate)
                if new_embedding:
                    embedding_cache[candidate.post_id] = new_embedding
                    embeddings.append(new_embedding)
        print(f"Generated embeddings for {len(embeddings)} candidates")

        weighted_embedding = apply_weights(embeddings, body.candidates)
        print("Weights applied to embeddings")

        result = opensearch_client.search_similar(weighted_embedding, body)
        print(f"Search returned {len(result)} results")

        recommendations = [hits for hits in result if hits]

        return {
            "statusCode": 200,
            "body": json.dumps({
                "recommendations": [json.loads(rec.model_copy(update={"status": "PROCESSED"}).model_dump_json()) for rec in recommendations],
            }),
        }

    except Exception as e:
        if isinstance(e, ValidationError) or isinstance(e, json.JSONDecodeError):
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid request", "errors": e.errors() if isinstance(e, ValidationError) else str(e)}),
            }

        print(f"Error processing request: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)}),
        }