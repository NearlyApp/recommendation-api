import os
import importlib


def lambda_handler(event, context):
    handler_name = os.environ.get("LAMBDA_HANDLER", "handlers.ingest_lambda_handler")

    module_name, function_name = handler_name.rsplit(".", 1)

    module = importlib.import_module(f"api.{module_name}")
    handler = getattr(module, function_name)

    return handler(event, context)
