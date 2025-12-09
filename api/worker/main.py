import json
import boto3
import os

from api.lib.pydantic.callback import CallbackIngestResult
from api.lib.utils import callback_ingest_result
from .lib.pydantic.data_models import DataModel, DataStatus
from .lib.data import put_data
from .lib.embeddings import embed_data
from .lib.opensearch import OpenSearchClient

sqs = boto3.client("sqs")
queue_url = os.getenv("QUEUE_URL")


def handler(event, context):
    """
    Lambda handler for SQS events with partial-batch failure reporting.
    """
    batch_failures = []

    for record in event.get("Records", []):
        print("Processing record:", record["messageId"])
        payload = json.loads(record["body"])
        print("Message body:", payload)
        # extract callback_url if exists then  remove it from payload
        callback_url = None
        if "callback_url" in payload:
            callback_url = payload.pop("callback_url")
            print("Callback URL found:", callback_url)

        parsed_data = DataModel(**payload)
        try:
            opensearch_client = OpenSearchClient()
            print("Opensearch client connected")

            # update to dynamodb with status PROCESSING
            result = put_data(
                parsed_data.model_copy(update={"status": DataStatus.processing.value})
            )

            print("Embedding data...")
            embeddings = embed_data(parsed_data)
            if not embeddings:
                raise Exception("Failed to generate embeddings.")

            print("Embeddings generated successfully")

            print("Saving embeddings to OpenSearch...")
            opensearch_client.save_embeddings(parsed_data, embeddings)
            print("Processed data successfully")

            # update to dynamodb with status PROCESSED
            result = put_data(
                parsed_data.model_copy(update={"status": DataStatus.processed.value})
            )

            # Send callback if URL is provided
            if callback_url:
                callback_ingest_result(
                    callback_url,
                    CallbackIngestResult(
                        post_id=parsed_data.post_id, status=DataStatus.processed
                    ),
                )

            if result is None:
                print(f"Failed to put data for ID {parsed_data.post_id}")
                batch_failures.append({"itemIdentifier": record["messageId"]})

        except Exception as e:
            print(f"Error processing {record['messageId']}: {e}")
            put_data(parsed_data.model_copy(update={"status": "FAILED"}))
            batch_failures.append({"itemIdentifier": record["messageId"]})

    return {"batchItemFailures": batch_failures}
