import json


def handler(event, context):
    """
    Lambda function handler for testing purposes.
    """
    print("Event received:", event)
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Test successful"})
    }
