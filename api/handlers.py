from lambdas.ingest import handler as ingest_handler
from worker.main import handler as worker_handler


def ingest_lambda_handler(event, context):
    return ingest_handler(event, context)


def worker_lambda_handler(event, context):
    return worker_handler(event, context)
