from lambdas.test import handler as test_handler
from lambdas.ingest import handler as ingest_handler


def test_lambda_handler(event, context):
    return test_handler(event, context)


def ingest_lambda_handler(event, context):
    return ingest_handler(event, context)
