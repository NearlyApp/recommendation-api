from ..worker.lib.opensearch import OpenSearchClient
from ..worker.lib.data import get_data, delete_data
import json


opensearch_client = OpenSearchClient()
print("Opensearch client connected")

def handler(event, context):
    try:
        method = event.get("httpMethod", "")
        data_id = event.get("pathParameters", {}).get("data_id", "")

        if not data_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "data_id is required"}),
            }

        if method == "GET":
            data = get_data(data_id)
            if not data:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "Data not found"}),
                }

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "data": json.loads(data.model_dump_json()),
                }),
            }

        elif method == "DELETE":
            # Delete from OpenSearch
            opensearch_client.delete_embeddings(data_id)

            deleted_data = delete_data(data_id)
            if not deleted_data:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "Data not found or already deleted"}),
                }

            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Data deleted successfully"}),
            }
    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)}),
        }