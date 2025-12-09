import boto3
import json
import os
from pydantic import ValidationError

from ..lib.pydantic.requests import IngestRequest
from ..worker.lib.pydantic.data_models import DataModel, DataStatus
from ..worker.lib.data import put_data

sqs = boto3.client("sqs")
queue_url = os.getenv("QUEUE_URL")


def handler(event, context):
    """
    Lambda function to parse incoming API request and send it to a standard SQS queue.
    """
    try:
        body = event.get("body", "{}")
        parsed_body = IngestRequest(**json.loads(body))

        response = sqs.send_message(
            QueueUrl=queue_url, MessageBody=parsed_body.model_dump_json()
        )
        # insert data status to DDB
        put_data(
            DataModel(
                **parsed_body.data.model_dump(), status=DataStatus.waiting_processing
            )
        )

        print("Message sent to SQS:", response)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Request sent successfully"}),
        }
    except Exception as e:
        if isinstance(e, ValidationError) or isinstance(e, json.JSONDecodeError):
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "message": "Invalid request",
                        "errors": (
                            e.errors() if isinstance(e, ValidationError) else str(e)
                        ),
                    }
                ),
            }
        print(f"Error sending message to SQS: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)}),
        }
