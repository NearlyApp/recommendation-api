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

            # upload to dynamodb
            result = put_data(parsed_data)

            print("Embedding data...")
            embeddings = embed_data(parsed_data)
            if not embeddings:
                raise Exception("Failed to generate embeddings.")

            print("Embeddings generated successfully")

            print("Saving embeddings to OpenSearch...")
            opensearch_client.save_embeddings(parsed_data, len(embeddings))

            # delete message from queue
            sqs.delete_message(
                QueueUrl=queue_url, ReceiptHandle=record["receiptHandle"]
            )

            if result is None:
                print(f"Failed to put data for ID {parsed_data.post_id}")
                batch_failures.append({"itemIdentifier": record["messageId"]})

        except Exception as e:
            print(f"Error processing {record['messageId']}: {e}")
            batch_failures.append({"itemIdentifier": record["messageId"]})

    return {"batchItemFailures": batch_failures}
