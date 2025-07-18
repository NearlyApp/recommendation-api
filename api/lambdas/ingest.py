import boto3
import json
import os

sqs = boto3.client('sqs')
queue_url = os.environ['QUEUE_URL']


def handler(event, context):
    """
    Lambda function to parse incoming API request and send it to a standard SQS queue.
    """
    print("Event received:", event)

    body = event.get('body', '{}')

    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=body
        )
        print("Message sent to SQS:", response)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Request sent successfully"})
        }
    except Exception as e:
        print(f"Error sending message to SQS: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal server error"})
        }
