from pydantic import ValidationError
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
                "body": json.dumps(
                    {
                        "data": json.loads(data.model_dump_json()),
                    }
                ),
            }

        elif method == "PATCH":
            body = event.get("body", "{}")
            update_data = json.loads(body)

            from ..worker.lib.pydantic.data_models import DataModelUpdate

            update_model = DataModelUpdate(**update_data)

            # Update in DynamoDB
            existing_data = get_data(data_id)
            if not existing_data:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "Data not found"}),
                }
            updated_data = existing_data.model_copy(
                update=update_model.model_dump(exclude_unset=True)
            )
            from ..worker.lib.data import put_data

            put_data(updated_data)

            # Update in OpenSearch
            opensearch_client.update_embeddings(data_id, update_model)

            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Data updated successfully"}),
            }

        elif method == "DELETE":
            # Delete from OpenSearch
            opensearch_client.delete_embeddings(data_id)

            deleted_data = delete_data(data_id)
            if not deleted_data:
                return {
                    "statusCode": 404,
                    "body": json.dumps(
                        {"message": "Data not found or already deleted"}
                    ),
                }

            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Data deleted successfully"}),
            }
    except Exception as e:
        print(f"Error processing request: {e}")
        # Catch pydantic errors and return 400
        if isinstance(e, ValidationError):
            return {
                "statusCode": 400,
                "body": json.dumps({"message": str(e.errors())}),
            }
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)}),
        }
