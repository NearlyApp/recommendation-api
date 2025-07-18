import json


def handler(event, context):
    """
    Lambda handler for SQS events with partial-batch failure reporting.
    """
    batch_failures = []

    for record in event.get('Records', []):
        try:
            print("Processing record:", record['messageId'])
            payload = json.loads(record['body'])
            print("Message body:", payload)
            # TODO: actual logic here
        except Exception as e:
            print(f"Error processing {record['messageId']}: {e}")
            batch_failures.append({"itemIdentifier": record['messageId']})

    return {"batchItemFailures": batch_failures}
