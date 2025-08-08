from opensearchpy import OpenSearch, AWSV4SignerAuth, RequestsHttpConnection
from cachetools import TTLCache, cached
import boto3
import os

from lib.pydantic.data_models import DataModel

opensearch_url = os.getenv("OPENSEARCH_ENDPOINT")
credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, "eu-west-1")
stage = os.getenv("STAGE", "dev")

connect_args = {
    "opensearch_url": opensearch_url,
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
    return OpenSearch(hosts=[opensearch_url], **connect_args)


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

    def save_embeddings(self, data: DataModel, vector_size: int):
        """
        Saves the embeddings for the given data model to OpenSearch.
        This method first ensures the index exists or is updated, then indexes the data.
        """
        # first upsert index
        self._upsert_index(vector_size)

        post_id = data.post_id
        self.client.index(index=self.index_name, id=post_id, body=data.model_dump())

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
