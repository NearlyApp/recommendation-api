import boto3
import json
import os
from pydantic import ValidationError

from lib.pydanctic.requests import IngestRequest

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
            QueueUrl=queue_url, MessageBody=parsed_body.data.model_dump_json()
        )

        print("Message sent to SQS:", response)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Request sent successfully"}),
        }
    except Exception as e:
        if isinstance(e, ValidationError):
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"message": "Invalid request", "errors": e.errors()}
                ),
            }
        print(f"Error sending message to SQS: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)}),
        }
