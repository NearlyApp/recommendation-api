from opensearchpy import OpenSearch, AWSV4SignerAuth, RequestsHttpConnection
from cachetools import TTLCache, cached
import boto3
import os
from urllib.parse import urlparse
import os

from .pydantic.data_models import DataModel
from api.lib.pydantic.requests import RecommendationRequest

opensearch_url = os.getenv("OPENSEARCH_ENDPOINT")
parsed_opensearch_url = urlparse(opensearch_url)
credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, "eu-west-1")
stage = os.getenv("STAGE", "dev")

connect_args = {
    "use_ssl": True,
    "verify_certs": True,
    "connection_class": RequestsHttpConnection,
    "http_auth": auth,
}

ttl_cache = TTLCache(maxsize=100, ttl=3600)


@cached(ttl_cache)
def get_opensearch_client():
    """
    Returns an OpenSearch client with caching.
    """
    return OpenSearch(
        hosts=[{"host": parsed_opensearch_url.hostname, "port": 443}], **connect_args
    )


class OpenSearchClient:
    def __init__(self):
        self.client = get_opensearch_client()
        self.index_name = f"nearly-data-{stage}"

    def _get_update_index_mapping(self, vector_size: int):
        """
        Returns the mapping for the OpenSearch index with the specified vector size.
        """
        return {
            "properties": {
                f"vector_{vector_size}": {
                    "type": "knn_vector",
                    "dimension": vector_size,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "faiss",
                    },
                }
            }
        }

    def _get_index_body(self, vector_size: int):
        properties = {
            "post_id": {"type": "keyword"},
            "text": {"type": "text"},
            **self._get_update_index_mapping(vector_size)["properties"],
            "metadata": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "geo_point",  # Opensearch auto accept objects with lat/lon floats
                    }
                },
            },
        }
        return {
            "settings": {
                "index.knn": True,
                "number_of_shards": 1,
                "number_of_replicas": 1,
            },
            "mappings": {
                "properties": properties,
            },
        }

    def _upsert_index(self, vector_size: int):
        """
        Create or update the OpenSearch index with the specified vector size.
        If not exists, it will create a new index with the appropriate settings and mapping.
        if exists, it will update the mapping if necessary.
        """
        try:
            if not self.client.indices.exists(index=self.index_name):
                print(
                    f"Creating index {self.index_name} with vector size {vector_size}"
                )
                self.client.indices.create(
                    index=self.index_name,
                    body=self._get_index_body(vector_size),
                )
                print(f"Index {self.index_name} created successfully.")

            mapping = self.client.indices.get_mapping(index=self.index_name)
            if (
                mapping[self.index_name]["mappings"]["properties"].get(
                    f"vector_{vector_size}"
                )
                is None
            ):
                print(
                    f"Updating index {self.index_name} with vector size {vector_size}"
                )
                self.client.indices.put_mapping(
                    index=self.index_name,
                    body=self._get_update_index_mapping(vector_size),
                )
                print(f"Mapping for index {self.index_name} updated successfully.")

        except Exception as e:
            print(f"Error upserting index {self.index_name}: {e}")
            raise e

    def save_embeddings(self, data: DataModel, embeddings: list[float]):
        """
        Saves the embeddings for the given data model to OpenSearch.
        This method first ensures the index exists or is updated, then indexes the data.
        """
        # first upsert index
        self._upsert_index(len(embeddings))

        post_id = data.post_id
        self.client.index(
            index=self.index_name,
            id=post_id,
            body={
                **data.model_dump(exclude={"status"}),
                f"vector_{len(embeddings)}": embeddings,
            },
        )
        print(f"Saved embeddings for post ID {post_id} successfully.")

    def delete_embeddings(self, post_id: str):
        """
        Deletes the embeddings for the given post ID from OpenSearch.
        """
        try:
            self.client.delete(index=self.index_name, id=post_id)
            print(f"Deleted embeddings for post ID {post_id} successfully.")
        except Exception as e:
            print(f"Error deleting embeddings for post ID {post_id}: {e}")
            raise e

    def search_similar(
        self, embeddings: list[float], parameters: RecommendationRequest
    ) -> list[DataModel]:
        """
        Searches for similar data models in OpenSearch based on the given embeddings.
        Returns a list of DataModel instances that are similar to the input embeddings.
        """
        try:
            knn_query = {
                "size": 50,
                "_source": {
                    "excludes": [f"vector_{len(embeddings)}"]  # exclude vector field from response
                },
                "query": {
                    "knn": {
                        f"vector_{len(embeddings)}": {
                            "vector": embeddings,
                            "k": 50,
                            "filter": {
                                "geo_distance": {
                                    "distance": parameters.distance,
                                    "metadata.location": {
                                        "lat": float(parameters.location.lat),
                                        "lon": float(parameters.location.lon),
                                    },
                                }
                            }
                        }
                    }
                },
            }

            print(f"Executing KNN query: {knn_query}")
            response = self.client.search(index=self.index_name, body=knn_query)
            hits = response.get("hits", {}).get("hits", [])
            results = [
                DataModel.model_validate(hit["_source"]) for hit in hits if "_source" in hit
            ]
            return results

        except Exception as e:
            print(f"Error searching for similar embeddings: {e}")
            raise e
