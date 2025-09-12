from worker.main import handler as worker_handler
from lambdas.ingest import handler as ingest_handler
from lambdas.data import handler as data_handler
from lambdas.recommendation import handler as recommendation_handler

def ingest_lambda_handler(event, context):
    return ingest_handler(event, context)

def data_lambda_handler(event, context):
    return data_handler(event, context)

def worker_lambda_handler(event, context):
    return worker_handler(event, context)

def recommendation_lambda_handler(event, context):
    return recommendation_handler(event, context)
