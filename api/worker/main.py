import json
import boto3
import os
from worker.lib.pydantic.data_models import DataModel
from worker.lib.data import put_data
from worker.lib.embeddings import embed_data
from worker.lib.opensearch import OpenSearchClient

sqs = boto3.client("sqs")
queue_url = os.getenv("QUEUE_URL")


def handler(event, context):
    """
    Lambda handler for SQS events with partial-batch failure reporting.
    """
    batch_failures = []

    for record in event.get("Records", []):
        try:
            print("Processing record:", record["messageId"])
            payload = json.loads(record["body"])
            print("Message body:", payload)
            parsed_data = DataModel(**payload)

            opensearch_client = OpenSearchClient()
            print("Opensearch client connected")

            # update to dynamodb with status PROCESSING
            result = put_data(
                DataModel(
                    post_id=parsed_data.post_id,
                    status="PROCESSING",
                    metadata=parsed_data.metadata,
                    text=parsed_data.text,
                    created_at=parsed_data.created_at,
                    updated_at=parsed_data.updated_at,
                )
            )

            print("Embedding data...")
            embeddings = embed_data(parsed_data)
            if not embeddings:
                raise Exception("Failed to generate embeddings.")

            print("Embeddings generated successfully")

            print("Saving embeddings to OpenSearch...")
            opensearch_client.save_embeddings(parsed_data, embeddings)

            # delete message from queue
            sqs.delete_message(
                QueueUrl=queue_url, ReceiptHandle=record["receiptHandle"]
            )
            print("Processed data successfully")

            # update to dynamodb with status PROCESSED
            result = put_data(
                DataModel(
                    post_id=parsed_data.post_id,
                    status="PROCESSED",
                    metadata=parsed_data.metadata,
                    text=parsed_data.text,
                    created_at=parsed_data.created_at,
                    updated_at=parsed_data.updated_at,
                )
            )

            if result is None:
                print(f"Failed to put data for ID {parsed_data.post_id}")
                batch_failures.append({"itemIdentifier": record["messageId"]})

        except Exception as e:
            print(f"Error processing {record['messageId']}: {e}")
            batch_failures.append({"itemIdentifier": record["messageId"]})

    return {"batchItemFailures": batch_failures}
